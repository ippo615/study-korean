
# -*- coding: utf-8 -*-

from typing import Union
from typing import List


class Syllable:
    """
    Represents a single Hangul syllable. It can be more easily analyzed than
    a single unicode character.

    Every syllable block is composed of 2 or 3 jamos, named:
        - jamo_initial
        - jamo_medial
        - jamo_final

    There are some 11,000+ combinations of jamos in unicode. This syllable class
    allows conversion from a list of 2 or 3 jamos to one of the 11,000+ unicode
    syllable blocks (and vice versa).

    See https://en.wikipedia.org/wiki/Korean_language_and_computers for more info.
    """
    INITIAL_JAMOS = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
    MEDIAL_JAMOS = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'
    FINAL_JAMOS = ' ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ'
    JAMO_NONE = ' '
    UNICODE_HANGUL_SYLLABLE_OFFSET = 44032
    UNICODE_INITIAL_JAMO_FACTOR = 588
    UNICODE_MEDIAL_JAMO_FACTOR = 28

    def __init__(self):
        self.syllable = ''
        self.jamo_initial = ''
        self.jamo_medial = ''
        self.jamo_final = ''

    @classmethod
    def from_syllable(cls, syllable: str):
        """Return a Syllable created from a unicode syllable block (ie 이 or 름)"""
        instance = cls()
        instance.syllable = syllable
        instance._decompose()
        return instance

    @classmethod
    def from_jamos(cls, jamo_initial: str, jamo_medial: str, jamo_final: str = ' '):
        """Return a Syllable created from indipendently specified jamos (ie ㅇ,ㅣ or ㄹ,ㅡ,ㅁ)"""
        instance = cls()
        instance.jamo_initial = jamo_initial
        instance.jamo_medial = jamo_medial
        instance.jamo_final = jamo_final
        instance._compose()
        return instance

    def append(self, jamo_final: str):
        """
        Sets the final jamo to the one specified.

        Raises ValueError if the final jamo has already been defined.
        """
        if self.jamo_final != self.JAMO_NONE:
            raise ValueError('Jamo final is %s -- there should not be a final jamo.')
        self.jamo_final = jamo_final
        self._compose()

    def endswith(self, jamo: str):
        """
        Returns true if the last jamo matches the one specified. If the syllable
        has no final jamo, this function treats the medial jamo as the final.
        """
        if self.jamo_final != ' ':
            return self.jamo_final == jamo
        return self.jamo_medial == jamo

    def _decompose(self):
        num = ord(self.syllable) - self.UNICODE_HANGUL_SYLLABLE_OFFSET
        n_initial = num // self.UNICODE_INITIAL_JAMO_FACTOR
        n_medial = (num % self.UNICODE_INITIAL_JAMO_FACTOR) // self.UNICODE_MEDIAL_JAMO_FACTOR
        n_final = (num % self.UNICODE_INITIAL_JAMO_FACTOR) % self.UNICODE_MEDIAL_JAMO_FACTOR
        self.jamo_initial = self.INITIAL_JAMOS[n_initial]
        self.jamo_medial = self.MEDIAL_JAMOS[n_medial]
        self.jamo_final = self.FINAL_JAMOS[n_final]

    def _compose(self):
        n_initial = self.INITIAL_JAMOS.index(self.jamo_initial) * self.UNICODE_INITIAL_JAMO_FACTOR
        n_medial = self.MEDIAL_JAMOS.index(self.jamo_medial) * self.UNICODE_MEDIAL_JAMO_FACTOR
        n_final = self.FINAL_JAMOS.index(self.jamo_final)
        self.syllable = chr(n_initial+n_medial+n_final+self.UNICODE_HANGUL_SYLLABLE_OFFSET)

    def __repr__(self):
        return '<%s %s (%s,%s,%s)>' % (
            self.__class__.__name__,
            self.syllable,
            self.jamo_initial,
            self.jamo_medial,
            self.jamo_final
        )


class WordForm:
    """
    A representation of a Korean word. It contains the full unicode representation
    in `string` and the same word represented as unicode sequence of jamos in
    `jamos`.
    """
    def __init__(self, string: str):
        self.string: str = string
        self.jamos: str = ''
        self.syllables: List[Syllable] = [Syllable.from_syllable(c) for c in self.string]
        self._build_jamo_sequence()

    def copy(self) -> "WordForm":
        return self.__class__(self.string)

    def append(self, suffix: str, merge_syllables=False):
        """
        Adds `suffix` to the end of this word form. If `merge_syllables` is True then
        it use the first character of the suffix as the last jamo of the last syllable
        in this word. Otherwise, by default, it will simply put attach`suffix`.

        Raises ValueError if the syllables cannot be merged and `merge_syllables`
        is True.
        """
        # Currently operates in place... should we make it return a new copy?
        if merge_syllables:
            if suffix[0] not in Syllable.INITIAL_JAMOS:
                raise ValueError('Cannot append: %s+%s (%s must start with one of: %s)' % (
                    self.string,
                    suffix,
                    suffix,
                    Syllable.INITIAL_JAMOS
                ))
            self.syllables[-1].append(suffix[0])
            self.syllables.extend([Syllable.from_syllable(c) for c in suffix[1:]])
        else:
            self.syllables.extend([Syllable.from_syllable(c) for c in suffix])
        self._build_jamo_sequence()
        self._syllabes_to_word()
        return self

    def _syllabes_to_word(self):
        self.string = ''.join([s.syllable for s in self.syllables])

    def _build_jamo_sequence(self):
        jamos = []
        for syllable in self.syllables:
            jamos.append(syllable.jamo_initial)
            jamos.append(syllable.jamo_medial)
            if syllable.jamo_final != syllable.JAMO_NONE:
                jamos.append(syllable.jamo_final)
        self.jamos = ''.join(jamos)

    def _repr_word(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            self.string
        )

    def _repr_jamo_sequence(self):
        return '<%s %s>' % (
            self.__class__.__name__,
            self.jamos
        )

    def __repr__(self):
        return '<%s "%s" %s>' % (
            self.__class__.__name__,
            self.string,
            self.jamos
        )


class Word:
    """
    Represents a single concept in a specific form.

    The lemma is the "dictionary form" of the word.
    The root is the stem of the word that particles and conjugated endings are
    attached to.
    The inflection is the "conjugated" form of the verb/adjective or the noun
    with particles attached.
    """
    def __init__(self, lemma: str):
        self.lemma: WordForm = WordForm(lemma)
        self.root: WordForm = WordForm(lemma)
        self.inflection: WordForm = WordForm(lemma)

    def copy(self) -> "Word":
        word = Word(self.lemma.string)
        word.root = self.root.copy()
        word.inflection = self.inflection.copy()
        return word


class Noun(Word):
    """Logical Noun. Currently does nothing different than a Word."""
    def __init__(self, lemma: str):
        Word.__init__(self, lemma)

    def __repr__(self):
        return '<%s %s = %s>' % (
            self.__class__.__name__,
            self.lemma,
            self.inflection
        )


class Topic(Noun):
    """A noun which indicates the topic of a statement (or the 은/는 particle)."""
    def __init__(self, word: Noun):
        Noun.__init__(self, word.lemma.string)
        if self.root.jamos.endswith(hangul_vowels):
            self.inflection.append('는')
        else:
            self.inflection.append('은')


class Subject(Noun):
    """A noun which indicates the subject of a statement (or the 이/가 particle)."""
    def __init__(self, word: Noun):
        Noun.__init__(self, word.lemma.string)
        if self.root.jamos.endswith(hangul_vowels):
            self.inflection.append('가')
        else:
            self.inflection.append('이')


class Object(Noun):
    """A noun which indicates the object of an action (or the 을/를 particle)."""
    def __init__(self, word: Noun):
        Noun.__init__(self, word.lemma.string)
        if self.root.jamos.endswith(hangul_vowels):
            self.inflection.append('를')
        else:
            self.inflection.append('을')


class Adjective(Word):
    """A descriptive predicate. Automatically computes the root/stem from the dictionary form."""
    def __init__(self, lemma: str):
        Word.__init__(self, lemma)
        if self.lemma.string.endswith('다'):
            self.root = WordForm(self.lemma.string[:-1])
        else:
            raise ValueError('%s does not end in 다 did you spell it correctly?')

    def __repr__(self):
        return '<%s %s root(%s)>' % (
            self.__class__.__name__,
            self.lemma.string,
            self.root.string
        )


class Verb(Word):
    """An action word. Automatically computes the root/stem from the dictionary form."""
    def __init__(self, lemma: str):
        Word.__init__(self, lemma)
        if self.lemma.string.endswith('다'):
            self.root = WordForm(self.lemma.string[:-1])
        else:
            raise ValueError('%s does not end in 다 did you spell it correctly?')

    def __repr__(self):
        return '<%s %s root(%s)>' % (
            self.__class__.__name__,
            self.lemma.string,
            self.root.string
        )


class Conjugation:
    """A conceptual representation of various verb forms."""
    def __repr__(self):
        return '<%s %s lemma(%s)>' % (
            self.__class__.__name__,
            self.word.inflection.string,
            self.word.lemma.string
        )


class PresentPolite(Conjugation):
    """The polite tone, present tense conjugation for verbs and adjectives."""
    def __init__(self, word: Union[Verb, Adjective]):
        self.word: Word = word.copy()
        self.word.inflection = self.word.root.copy()
        if self.word.root.jamos.endswith(hangul_vowels):
            self.word.inflection.append('ㅂ니다', True)
        else:
            self.word.inflection.append('습니다')


class PresentTense(Conjugation):
    def __init__(self, word: Union[Verb, Adjective]):
        self.word: Word = word.copy()

    def informalLow(self):
        self.word.inflection = self.word.root.copy()
        if self.word.root.jamos.endswith(hangul_consonants):
            self.word.inflection.append('는다')
        else:
            self.word.inflection.append('ㄴ다', True)


class PastTense(Conjugation):
    # NOTE THIS IS UNFINISHED!
    def __init__(self, word: Union[Verb, Adjective]):
        self.word: Word = word.copy()

    def _build_base_inflection(self):
        if self.word.root.string.endswith('하'):
            pass

        # add a ㅏ
        elif self.word.root.jamos.endswith(('ㅏ','ㅗ','ㅑ','ㅛ')):
            # 아+아 = 아
            if self.word.root.jamos.endswith('ㅏ'):
                pass
            # 오 + 아 = 와
            if self.word.root.jamos.endswith('ㅗ'):
                self.word.inflection.jamos[-i] = 'ㅘ'

        # add a ㅓ
        else:
            if self.word.root.jamos.endswith('ㅜ'):
                self.word.inflection.jamos[-i] = 'ㅝ'
            if self.word.root.jamos.endswith('ㅣ'):
                self.word.inflection.jamos[-i] = 'ㅕ'
            if self.word.root.jamos.endswith('ㅓ'):
                pass
            if self.word.root.jamos.endswith('ㅕ'):
                self.word.inflection.jamos[-i] = 'ㅕ'

def stuff1():
    be = Verb('이다')
    eat = Verb('먹다')
    print(PresentPolite(be))
    print(PresentPolite(eat))

    i = Noun('저')
    print(Subject(i))
    print(Object(i))

    korea = Noun('한국')
    city = Noun('도시')
    name = Noun('이름')
    man = Noun('남자')
    woman = Noun('여자')
    this = Noun('이')
    that = Noun('그')
    that_over_there = Noun('저')
    thing = Noun('것')
    chair = Noun('의자')
    table = Noun('탁자')
    teacher = Noun('선생님')
    bed = Noun('침대')
    house = Noun('집')
    car = Noun('차')
    person = Noun('사람')
    book = Noun('책')
    computer = Noun('컴퓨터')
    tree = Noun('나무')
    sofa = Noun('소파')
    china = Noun('중국')
    japan = Noun('일본')
    door = Noun('문')
    doctor = Noun('의사')
    student = Noun('학생')

    be_at = Verb('있다')
    have = Verb('있다')

    print(Subject(i))
    print(Object(this))
    print(PresentPolite(have))

    # Todo -- make a class?
    # class Idea:
    # class Phrase(Idea)
    # class x_has_y() .. init(x:Phrase, y:Phrase)
    def x_has_y(x, y):
        return ' '.join([
            Topic(x).inflection.string,
            Subject(y).inflection.string,
            PresentPolite(have).word.inflection.string
        ])

    print(x_has_y(student, book))
    print(x_has_y(teacher, table))
    print(x_has_y(doctor, chair))

    # Text to speech
    from win32com.client import Dispatch
    speak = Dispatch("SAPI.SpVoice")

    for v in speak.GetVoices():
        print(v.GetDescription())
    speak.Voice = speak.GetVoices().Item(3)
    speak.Rate = 0.5

    print(speak.Speak("Hello world!"))
    print(speak.Speak(x_has_y(doctor, chair)))

    # 저 = I, me (formal)
    # 나 = I, me (informal)
    # 이것 = this (thing)
    # 그것 = that (thing)
    # 저것 = that (thing)
    # 이다 = to be
    # 네 = yes
    # 아니 = no

if __name__ == '__main__':

    hangul_vowels = tuple('ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ')
    hangul_consonants = tuple('ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ')

    eat = Verb('먹다')
    learn = Verb('베우다')
    verbs = [eat, learn]

    for v in verbs:
        p = PresentTense(v)
        p.informalLow()
        print(p)
