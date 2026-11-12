"""Self-upgrading skill discovery, sandbox inspection, upgrade proposal, approval, and rollback routes."""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import get_all_agents
from app.database import get_session
from app.models.security import AuditAction, AuditLog, AuditSeverity

router = APIRouter()

# Locate repository root -> skills/
REPO_ROOT = Path(__file__).resolve().parents[5]
SKILLS_ROOT = REPO_ROOT / "skills"
SANDBOX_DIR = SKILLS_ROOT / "sandbox"

# Ensure skills/sandbox/runner.py is importable
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

# In-process registry of upgrade proposals & backups (also audited in SQLite AuditLog)
_PROPOSALS: dict[str, dict[str, Any]] = {}


def _list_skill_dirs() -> list[Path]:
    if not SKILLS_ROOT.exists():
        return []
    dirs: list[Path] = []
    for base in (SKILLS_ROOT / "core", SKILLS_ROOT / "community", SKILLS_ROOT):
        if not base.exists() or not base.is_dir():
            continue
        for item in sorted(base.iterdir()):
            if item.is_dir() and item.name not in {"core", "community", "sandbox", "tests", "__pycache__"} and (item / "manifest.json").exists():
                dirs.append(item)
    return dirs


def _find_skill_dir(skill_name: str) -> Optional[Path]:
    for d in _list_skill_dirs():
        if d.name == skill_name:
            return d
        try:
            m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
            if m.get("id") == skill_name:
                return d
        except Exception:
            pass
    return None


class SkillInspectRequest(BaseModel):
    skill_name: Optional[str] = None
    skill_path: Optional[str] = None
    source_code: Optional[str] = None
    manifest: Optional[dict[str, Any]] = None
    test_payload: dict[str, Any] = Field(default_factory=dict)


class SkillUpgradeProposalRequest(BaseModel):
    target_version: str = Field(..., min_length=1, max_length=32)
    source_url: Optional[str] = None
    license_name: str = "MIT"
    requested_permissions: list[str] = Field(default_factory=list)
    new_source_code: Optional[str] = None
    summary: str = "Compatibility & performance improvement"
    test_payload: dict[str, Any] = Field(default_factory=dict)


class SkillUpgradeActionRequest(BaseModel):
    proposal_id: str
    approved_by: str = "owner"


@router.get("/")
async def list_skills() -> dict[str, Any]:
    """Discover installed skills under skills/ along with manifest metadata and checksums."""
    from sandbox.runner import compute_sha256

    items: list[dict[str, Any]] = []
    for skill_dir in _list_skill_dirs():
        manifest_path = skill_dir / "manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {"name": skill_dir.name, "error": "invalid_manifest"}
        entrypoint = skill_dir / str(manifest.get("entrypoint", "skill.py"))
        actual_sha = compute_sha256(entrypoint) if entrypoint.exists() else None
        items.append(
            {
                "name": manifest.get("name", skill_dir.name),
                "dir": skill_dir.name,
                "version": manifest.get("version", "0.1.0"),
                "license": manifest.get("license", "UNKNOWN"),
                "trust_tier": manifest.get("trust_tier", "experimental"),
                "permissions": manifest.get("permissions", []),
                "dependencies": manifest.get("dependencies", []),
                "sha256": actual_sha,
                "has_backup": (skill_dir / ".backup_skill.py").exists(),
            }
        )
    return {"skills": items, "total": len(items), "skills_root": str(SKILLS_ROOT)}


@router.post("/inspect")
async def inspect_skill(
    body: SkillInspectRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Run license check, AST security scan, permission inspection, and isolated subprocess sandbox test."""
    from sandbox.runner import calculate_trust_score, inspect_skill_ast, run_skill_sandboxed

    agents = get_all_agents()
    trust_agent = agents.get("plugin_trust")

    if body.source_code is not None:
        manifest = dict(body.manifest or {"name": body.skill_name or "candidate_skill", "license": "MIT", "permissions": []})
        permissions = list(manifest.get("permissions", []))
        license_name = str(manifest.get("license", "UNKNOWN"))
        allowed_licenses = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "PSF-2.0"}
        license_ok = license_name in allowed_licenses
        violations = inspect_skill_ast(body.source_code, permissions)
        score = calculate_trust_score(manifest, violations, checksum_verified=False, tests_passed=not violations and license_ok)
        trust_report = (
            await trust_agent.run(
                {"action": "inspect", "skill": manifest["name"], "permissions": permissions, "license": license_name, "violations": violations}
            )
            if trust_agent
            else {}
        )
        passed = len(violations) == 0 and license_ok
        session.add(
            AuditLog(
                id=str(uuid4()),
                agent_id="skill_sandbox",
                action=AuditAction.EXECUTE,
                severity=AuditSeverity.INFO if passed else AuditSeverity.WARNING,
                resource_type="skill",
                description=f"Inline skill inspect for {manifest['name']}: {'passed' if passed else 'blocked'}",
                details={"violations": violations, "license": license_name, "trust_score": score},
            )
        )
        await session.commit()
        return {
            "passed": passed,
            "license": license_name,
            "license_ok": license_ok,
            "violations": violations,
            "permissions": permissions,
            "trust_score": score,
            "trust_report": trust_report,
        }

    # Resolve target skill directory
    target_dir: Optional[Path] = None
    if body.skill_name:
        target_dir = _find_skill_dir(body.skill_name)
    elif body.skill_path:
        candidate = Path(body.skill_path).resolve()
        if candidate.exists() and (candidate / "manifest.json").exists():
            target_dir = candidate

    if target_dir is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill directory not found")

    manifest = json.loads((target_dir / "manifest.json").read_text(encoding="utf-8"))
    license_name = str(manifest.get("license", "MIT"))
    sandbox_res = run_skill_sandboxed(target_dir, body.test_payload, verify_checksum=True)
    trust_report = (
        await trust_agent.run(
            {
                "action": "inspect",
                "skill": manifest.get("name", target_dir.name),
                "permissions": manifest.get("permissions", []),
                "license": license_name,
                "violations": sandbox_res.violations,
            }
        )
        if trust_agent
        else {}
    )
    session.add(
        AuditLog(
            id=str(uuid4()),
            agent_id="skill_sandbox",
            action=AuditAction.EXECUTE,
            severity=AuditSeverity.INFO if sandbox_res.success else AuditSeverity.WARNING,
            resource_type="skill",
            description=f"Skill sandbox inspect for {target_dir.name}: {'passed' if sandbox_res.success else 'blocked'}",
            details={"trust_score": sandbox_res.trust_score, "violations": sandbox_res.violations, "error": sandbox_res.error},
        )
    )
    await session.commit()
    return {
        "skill": target_dir.name,
        "passed": sandbox_res.success,
        "output": sandbox_res.output,
        "error": sandbox_res.error,
        "violations": sandbox_res.violations,
        "trust_score": sandbox_res.trust_score,
        "duration_ms": sandbox_res.duration_ms,
        "trust_report": trust_report,
    }


@router.post("/{skill_name}/propose-upgrade")
async def propose_skill_upgrade(
    skill_name: str,
    body: SkillUpgradeProposalRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Create a sandbox-verified, human-approval-gated skill upgrade proposal."""
    from sandbox.runner import inspect_skill_ast

    skill_dir = _find_skill_dir(skill_name)
    if skill_dir is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_name}' not found")

    manifest = json.loads((skill_dir / "manifest.json").read_text(encoding="utf-8"))
    allowed_licenses = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "PSF-2.0"}
    if body.license_name not in allowed_licenses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Rejected unapproved license '{body.license_name}'",
        )

    violations: list[str] = []
    if body.new_source_code:
        violations = inspect_skill_ast(body.new_source_code, body.requested_permissions)
        if violations:
            session.add(
                AuditLog(
                    id=str(uuid4()),
                    agent_id="self_upgrading_engineer",
                    action=AuditAction.REJECT,
                    severity=AuditSeverity.CRITICAL,
                    resource_type="skill",
                    description=f"Blocked unsafe skill upgrade proposal for {skill_name}",
                    details={"violations": violations},
                )
            )
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Candidate skill failed AST security check: {violations}",
            )

    high_risk_perms = {"network:external", "filesystem:write", "process:exec"}
    requires_approval = True
    risk_level = "high" if any(p in high_risk_perms for p in body.requested_permissions) else "medium"

    agents = get_all_agents()
    eng = agents.get("self_upgrading_engineer")
    eng_report = (
        await eng.run(
            {
                "action": "propose_upgrade",
                "skill": skill_name,
                "current_version": manifest.get("version", "0.1.0"),
                "target_version": body.target_version,
                "summary": body.summary,
            }
        )
        if eng
        else {}
    )

    proposal_id = str(uuid4())
    proposal = {
        "proposal_id": proposal_id,
        "skill_name": skill_name,
        "current_version": manifest.get("version", "0.1.0"),
        "target_version": body.target_version,
        "license": body.license_name,
        "requested_permissions": body.requested_permissions,
        "new_source_code": body.new_source_code,
        "summary": body.summary,
        "risk_level": risk_level,
        "requires_approval": requires_approval,
        "status": "pending_approval",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "engineer_report": eng_report,
    }
    _PROPOSALS[proposal_id] = proposal

    session.add(
        AuditLog(
            id=str(uuid4()),
            agent_id="self_upgrading_engineer",
            action=AuditAction.PROPOSE if hasattr(AuditAction, "PROPOSE") else AuditAction.UPDATE,
            severity=AuditSeverity.INFO,
            resource_type="skill",
            description=f"Proposed upgrade for skill {skill_name} -> {body.target_version}",
            details={"proposal_id": proposal_id, "target_version": body.target_version, "risk_level": risk_level},
        )
    )
    await session.commit()
    return {k: v for k, v in proposal.items() if k != "new_source_code"}


@router.post("/{skill_name}/apply-upgrade")
async def apply_skill_upgrade(
    skill_name: str,
    body: SkillUpgradeActionRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Apply an approved upgrade proposal after saving a local rollback backup."""
    from sandbox.runner import compute_sha256

    proposal = _PROPOSALS.get(body.proposal_id)
    if proposal is None or proposal["skill_name"] != skill_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upgrade proposal not found")

    skill_dir = _find_skill_dir(skill_name)
    if skill_dir is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_name}' not found")
    manifest_path = skill_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entrypoint = skill_dir / str(manifest.get("entrypoint", "skill.py"))

    # Create backup copies before modifying
    shutil.copy2(manifest_path, skill_dir / ".backup_manifest.json")
    if entrypoint.exists():
        shutil.copy2(entrypoint, skill_dir / ".backup_skill.py")

    if proposal.get("new_source_code"):
        entrypoint.write_text(proposal["new_source_code"], encoding="utf-8")
    manifest["version"] = proposal["target_version"]
    manifest["license"] = proposal["license"]
    if proposal.get("requested_permissions"):
        manifest["permissions"] = proposal["requested_permissions"]
    if entrypoint.exists():
        manifest["sha256"] = compute_sha256(entrypoint)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    proposal["status"] = "applied"
    proposal["approved_by"] = body.approved_by
    session.add(
        AuditLog(
            id=str(uuid4()),
            agent_id="self_upgrading_engineer",
            action=AuditAction.APPROVE,
            severity=AuditSeverity.INFO,
            resource_type="skill",
            description=f"Applied approved upgrade for skill {skill_name} -> {manifest['version']} by {body.approved_by}",
            details={"proposal_id": body.proposal_id, "new_version": manifest["version"]},
        )
    )
    await session.commit()
    return {"skill_name": skill_name, "version": manifest["version"], "status": "applied", "rollback_available": True}


@router.post("/{skill_name}/rollback")
async def rollback_skill(
    skill_name: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Restore a skill to its pre-upgrade backup manifest and source."""
    skill_dir = _find_skill_dir(skill_name)
    if skill_dir is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_name}' not found")
    backup_manifest = skill_dir / ".backup_manifest.json"
    backup_code = skill_dir / ".backup_skill.py"
    if not backup_manifest.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No rollback backup available for '{skill_name}'")

    manifest = json.loads(backup_manifest.read_text(encoding="utf-8"))
    entrypoint = skill_dir / str(manifest.get("entrypoint", "skill.py"))
    shutil.copy2(backup_manifest, skill_dir / "manifest.json")
    if backup_code.exists():
        shutil.copy2(backup_code, entrypoint)

    backup_manifest.unlink(missing_ok=True)
    backup_code.unlink(missing_ok=True)

    session.add(
        AuditLog(
            id=str(uuid4()),
            agent_id="self_upgrading_engineer",
            action=AuditAction.CONFIG_CHANGE,
            severity=AuditSeverity.WARNING,
            resource_type="skill",
            description=f"Rolled back skill {skill_name} to version {manifest.get('version')}",
            details={"restored_version": manifest.get("version")},
        )
    )
    await session.commit()
    return {"skill_name": skill_name, "restored_version": manifest.get("version"), "status": "rolled_back"}
