"""Small original Devanagari pronunciation helper, without a GPL phonemizer.

This is approximate orthographic pronunciation, not a learned language model.
Users can override words in the local pronunciation dictionary. No training or
full Hindi/Hinglish pronunciation-quality claim follows from this helper.
"""
import unicodedata

CONSONANTS = dict(zip('कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह',
    ['k','kʰ','ɡ','ɡʰ','ŋ','tʃ','tʃʰ','dʒ','dʒʰ','ɲ','ʈ','ʈʰ','ɖ','ɖʰ','ɳ','t','tʰ','d','dʰ','n','p','pʰ','b','bʰ','m','j','ɾ','l','ʋ','ʃ','ʂ','s','h']))
VOWELS = dict(zip('अआइईउऊऋएऐओऔ', ['ə','ɑː','ɪ','iː','ʊ','uː','ɾɪ','eː','ɛː','oː','ɔː']))
MARKS = dict(zip('ािीुूृेैोौ', ['ɑː','ɪ','iː','ʊ','uː','ɾɪ','eː','ɛː','oː','ɔː']))


def pronounce(word):
    result, inherent = [], False
    for character in unicodedata.normalize('NFC', word):
        if character in CONSONANTS:
            result.extend([CONSONANTS[character], 'ə'])
            inherent = True
        elif character in MARKS:
            if inherent:
                result.pop()
            result.append(MARKS[character])
            inherent = False
        elif character == '्':
            if inherent:
                result.pop()
            inherent = False
        elif character in VOWELS:
            result.append(VOWELS[character])
            inherent = False
        elif character in {'ं', 'ँ'}:
            result.append('̃')
            inherent = False
        elif character == 'ः':
            result.append('h')
            inherent = False
    if inherent and len(result) > 2:
        result.pop()
    return ''.join(result)
