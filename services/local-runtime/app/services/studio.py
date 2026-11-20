"""Fixed native ComfyUI graphs; no custom-code/API nodes, cloud fallback or replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import get_settings
from app.core.provider_store import ProviderVault


class Configuration(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    enabled: bool = Field(default=False, strict=True)
    base_url: str = Field(default='http://127.0.0.1:8188', max_length=200)
    image_checkpoint: str = Field(default='', max_length=180)
    video_unet: str = Field(default='', max_length=180)
    video_clip: str = Field(default='', max_length=180)
    video_vae: str = Field(default='', max_length=180)

    @field_validator('base_url')
    @classmethod
    def endpoint(cls, value):
        url = urlsplit(value)
        if (url.scheme != 'http' or url.hostname not in {'127.0.0.1', 'localhost', '::1'} or
            url.username or url.password or url.path not in {'', '/'} or url.query or url.fragment or
            (url.port is not None and not 1 <= url.port <= 65535)):
            raise ValueError('Use a local loopback ComfyUI endpoint without credentials or a path')
        return value.rstrip('/')

    @field_validator('image_checkpoint', 'video_unet', 'video_clip', 'video_vae')
    @classmethod
    def model_name(cls, value):
        if value and (value.startswith('/') or '\\' in value or ':' in value or any(p in {'.', '..', ''} for p in value.split('/')) or any(ord(c) < 32 for c in value)):
            raise ValueError('Use a relative model name from your ComfyUI model inventory')
        return value


class Generation(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    request_key: str = Field(min_length=1, max_length=64, pattern=r'^[a-zA-Z0-9_-]+$')
    kind: Literal['image', 'video']
    prompt: str = Field(min_length=1, max_length=2000)
    negative_prompt: str = Field(default='', max_length=1000)
    seed: int = Field(default=0, ge=0, le=2**32-1, strict=True)
    configuration_fingerprint: str = Field(pattern=r'^[a-f0-9]{64}$')
    reviewed: Literal[True]

    @field_validator('reviewed', mode='before')
    @classmethod
    def exact_confirmation(cls, value):
        if type(value) is not bool or not value:
            raise ValueError('Explicit review confirmation is required')
        return value


def vault():
    s = get_settings()
    return ProviderVault(Path(s.provider_config_path).with_name('studio-config.enc'), s.encryption_key,
                         key_domain=b'javo-studio-v1\0')


def configuration():
    value = Configuration.model_validate(vault().read()['settings']).model_dump()
    value['fingerprint'] = hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    return value


async def request(cfg, method, route, *, payload=None, params=None, limit=1024*1024):
    async with httpx.AsyncClient(timeout=httpx.Timeout(10, connect=3), trust_env=False, follow_redirects=False) as client:
        async with client.stream(method, cfg['base_url']+route, json=payload, params=params,
                                 headers={'Accept-Encoding': 'identity'}) as response:
            response.raise_for_status()
            if response.headers.get('content-encoding', 'identity').lower() not in {'identity', ''}:
                raise ValueError('Compressed response is unsupported')
            data = bytearray()
            async for chunk in response.aiter_bytes():
                data.extend(chunk)
                if len(data) > limit:
                    raise ValueError('Generation service response exceeds its limit')
            return bytes(data)


async def json_request(cfg, method, route, **kwargs):
    return json.loads(await request(cfg, method, route, **kwargs))


def graph(cfg, body, job_id):
    def node(kind, **inputs):
        return {'class_type': kind, 'inputs': inputs}
    prefix = 'Javo/'+job_id
    if body.kind == 'image':
        return {
            '1': node('CheckpointLoaderSimple', ckpt_name=cfg['image_checkpoint']),
            '2': node('CLIPTextEncode', text=body.prompt, clip=['1', 1]),
            '3': node('CLIPTextEncode', text=body.negative_prompt, clip=['1', 1]),
            '4': node('EmptyLatentImage', width=512, height=512, batch_size=1),
            '5': node('KSampler', model=['1', 0], positive=['2', 0], negative=['3', 0], latent_image=['4', 0],
                      seed=body.seed, steps=20, cfg=7.0, sampler_name='euler', scheduler='normal', denoise=1.0),
            '6': node('VAEDecode', samples=['5', 0], vae=['1', 2]),
            '7': node('SaveImage', images=['6', 0], filename_prefix=prefix),
        }
    return {
        '1': node('UNETLoader', unet_name=cfg['video_unet'], weight_dtype='default'),
        '2': node('CLIPLoader', clip_name=cfg['video_clip'], type='wan', device='default'),
        '3': node('VAELoader', vae_name=cfg['video_vae']),
        '4': node('CLIPTextEncode', text=body.prompt, clip=['2', 0]),
        '5': node('CLIPTextEncode', text=body.negative_prompt, clip=['2', 0]),
        '6': node('EmptyHunyuanLatentVideo', width=832, height=480, length=49, batch_size=1),
        '7': node('ModelSamplingSD3', model=['1', 0], shift=8.0),
        '8': node('KSampler', model=['7', 0], positive=['4', 0], negative=['5', 0], latent_image=['6', 0],
                  seed=body.seed, steps=20, cfg=6.0, sampler_name='uni_pc', scheduler='simple', denoise=1.0),
        '9': node('VAEDecode', samples=['8', 0], vae=['3', 0]),
        '10': node('CreateVideo', images=['9', 0], fps=16),
        '11': node('SaveVideo', video=['10', 0], filename_prefix=prefix, format='auto'),
    }


async def preflight(cfg, kind):
    if not cfg['enabled']:
        raise ValueError('Local generation is disabled')
    classes = ['CheckpointLoaderSimple', 'CLIPTextEncode', 'EmptyLatentImage', 'KSampler', 'VAEDecode', 'SaveImage'] if kind == 'image' else ['UNETLoader', 'CLIPLoader', 'VAELoader', 'CLIPTextEncode', 'EmptyHunyuanLatentVideo', 'ModelSamplingSD3', 'KSampler', 'VAEDecode', 'CreateVideo', 'SaveVideo']
    inventories = {}
    for name in classes:
        value = await json_request(cfg, 'GET', '/object_info/'+name)
        if name not in value:
            raise ValueError('A required native generation node is unavailable')
        inventories[name] = value[name]
    models = [('CheckpointLoaderSimple', 'ckpt_name', cfg['image_checkpoint'])] if kind == 'image' else [
        ('UNETLoader', 'unet_name', cfg['video_unet']), ('CLIPLoader', 'clip_name', cfg['video_clip']), ('VAELoader', 'vae_name', cfg['video_vae'])]
    for cls, field, selected in models:
        choices = inventories[cls]['input']['required'][field][0]
        if not selected or selected not in choices:
            raise ValueError('Select installed compatible models from the generation service inventory')
    return {'ready': True, 'generation_verified': False, 'kind': kind}


def artifact_root():
    return Path(get_settings().provider_config_path).resolve().parent/'generated-media'


def safe_artifact(metadata, kind):
    filename = metadata.get('filename', '')
    subfolder = metadata.get('subfolder', '')
    if (not isinstance(filename, str) or len(filename) > 200 or not filename or
        any(c in filename for c in '/\\:') or filename in {'.', '..'} or
        not isinstance(subfolder, str) or len(subfolder) > 200 or '\\' in subfolder or ':' in subfolder or
        PurePosixPath(subfolder).is_absolute() or '..' in PurePosixPath(subfolder).parts or metadata.get('type') != 'output'):
        raise ValueError('Unsafe generated artifact reference')
    extension = Path(filename).suffix.lower()
    if extension not in ({'.png', '.jpg', '.jpeg', '.webp'} if kind == 'image' else {'.mp4', '.webm'}):
        raise ValueError('Unexpected generated artifact format')
    return {'filename': filename, 'subfolder': subfolder, 'type': 'output'}, extension


def media_type(data, extension):
    if extension == '.png' and data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if extension in {'.jpg', '.jpeg'} and data.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if extension == '.webp' and data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return 'image/webp'
    if extension == '.mp4' and len(data) > 12 and data[4:8] == b'ftyp':
        return 'video/mp4'
    if extension == '.webm' and data.startswith(b'\x1aE\xdf\xa3'):
        return 'video/webm'
    raise ValueError('Artifact bytes do not match the expected media format')
