from collections import OrderedDict
import time

import requests
import bs4


class Translation():
    def __init__(self, meaning, translation):
        self.meaning = meaning
        self.translation = translation

    def __str__(self):
        return '%s: %s' % (self.meaning, self.translation)


class Translator():
    def __init__(self, word, target_language):
        self.word = word
        self.target_language = target_language
        self.meanings = []
        self._run()

    def _run(self):
        # Download the wiktionary page for this word
        r = requests.get('https://en.wiktionary.org/wiki/%s' % self.word)
        soup = bs4.BeautifulSoup(r.content, features='lxml')

        # Get the translation sections
        # We're looking for an id so there should only be 1 but .select
        # returns a list so we'll just take the 1st element of the list.
        # TODO: handle multiple translation sections
        # Wrong! https://en.wiktionary.org/wiki/dog#Translations
        # There are multiples translations id'd as: #Transtions_2, etc...
        # The one we want -- noun, links to anohter page:
        # https://en.wiktionary.org/wiki/dog/translations#Noun
        translation_title = soup.select('#Translations')[0].parent
        translation_nodes = []
        next_node = translation_title.nextSibling
        while True:
            next_node = next_node.nextSibling
            if next_node is None:
                break
            if isinstance(next_node, bs4.Tag):
                if next_node.name in ["h1", "h2", "h3", "h4", "h5"]:
                    break
                translation_nodes.append(next_node)

        # Parse the translation sections into useful content
        for node in translation_nodes:
            # Not every translation has these ids.
            # https://en.wiktionary.org/wiki/big#Translations
            # meaning = node['id'].replace('Translations-', '')
            # if 'class' not in node.attrs:
            #     continue
            if 'NavFrame' not in node.attrs['class']:
                continue
            nav_head = node.select('.NavHead')[0]
            meaning = nav_head.find(text=True, recursive=False)
            for li in node.select('li'):
                text = li.get_text(strip=True)
                parts = text.split(':')
                language = parts[0]
                translation = ':'.join(parts[1:])
                if language == self.target_language:
                    if translation:
                        self.meanings.append(Translation(meaning, translation))

    def __str__(self):
        return '%s:\n\t%s' % (
            self.word,
            '\n\t'.join(['%s' % m for m in self.meanings])
        )


class BableTranslator():
    def __init__(self, word, target_language):
        self.word = word
        self.target_language = target_language
        self.meanings = []
        self._run()

    def _run(self):
        r = requests.get('https://babelnet.org/search?word=%s&lang=EN&langTrans=%s' % (self.word, self.target_language))
        soup = bs4.BeautifulSoup(r.content, features='lxml')
        # Take the first result because we are lazy
        # The 2nd <h3> has the translation in the target language
        result = soup.select('.result')[0]
        definition = result.select('.result-definition')[0]
        meaning = definition.select('.def')[0].text.strip()
        heading = result.select('h3')[1]
        text = heading.select('a')[0].text
        words = '; '.join([s.strip() for s in text.split('•')])
        self.meanings.append(Translation(meaning, words))

    def __str__(self):
        return '%s:\n\t%s' % (
            self.word,
            '\n\t'.join(['%s' % m for m in self.meanings])
        )


def download_wikitionary_words():
    with open('tools/most_common_words.txt') as f:
        words = f.readlines()

    for word in words:
        word = word.strip().lower()
        if not word:
            continue
        print(word)
        try:
            t = Translator(word, 'Korean')
        except Exception as e:
            print('Error with %s' % word)
            print(e)
        else:
            with open('tools/output.txt', 'a', encoding="utf-8") as f:
                f.write('%s\n\n' % t)
            print(t)
        time.sleep(0.5)


class Section():
    def __init__(self, heading, contents):
        self.heading = heading
        self.contents = contents
        self.children = []


class Document():
    LEVEL_SEPARATOR = ' // '

    def __init__(self, soup):
        self.soup = soup
        self.nodes_by_toc = OrderedDict()

    def build_nodes_by_toc(self, clean_text=lambda x: x.lower().strip()):
        nodes = OrderedDict()
        headings = self.soup.select('h1, h2, h3, h4, h5, h6')
        stack = []
        last_level = 0
        for h in headings:
            current_level = int(h.name.strip('h'))
            # Go one level deeper (ie keep the last element in the path)
            if current_level > last_level:
                pass
            # Stay at the current level (ie the last element is a sibling)
            if current_level == last_level:
                stack.pop()
            # Go up one level (ie the last element is the parent)
            if current_level < last_level:
                stack.pop()
                stack.pop()
            # Insert the new element on the stack
            stack.append(clean_text(h.text.strip()))
            path = self.LEVEL_SEPARATOR.join(stack)
            nodes[path] = h
            # print('%s: %s - %s' % (path, h.name, clean_text(h.text.strip())))
            last_level = current_level
        self.nodes_by_toc = nodes

    def get_toc_pretty(self):
        headings = self.nodes_by_toc.keys()
        lines = []
        for h in headings:
            parts = h.split(self.LEVEL_SEPARATOR)
            most_significant = parts[-1]
            lines.append('  '*len(parts)+most_significant)
        return lines

    def get_toc(self):
        return self.nodes_by_toc.keys()

    def extract_section(self, heading):
        # OrderedDicts dont support a .next method so we
        # need to do wierd stuff to get the "next" element.
        # https://stackoverflow.com/questions/12328184/how-to-get-the-next-item-in-an-ordereddict
        start_node = self.nodes_by_toc[heading]
        start_node_level = heading.count(self.LEVEL_SEPARATOR)
        end_node = None
        past_start = False
        for key in self.nodes_by_toc:
            if key == heading:
                past_start = True
                continue
            if not past_start:
                continue
            node_level = key.count(self.LEVEL_SEPARATOR)
            if node_level <= start_node_level:
                end_node = self.nodes_by_toc[key]
                break

        # Apparently you cannot iterate over node.next_siblings
        # but you can iterate over list(...)
        section = self.soup.new_tag('div')
        for node in list(start_node.next_siblings):
            if node is end_node:
                break
            section.append(node)
        return section

    def find_heading(self, parts):
        for h in self.nodes_by_toc.keys():
            try:
                start = 0
                for p in parts:
                    start = h.index(p, start)
            except ValueError:
                # no string match
                pass
            else:
                return h
        # Uh oh. No match.
        raise ValueError('Unable to find matching heading containing: %s' % parts)


class WiktionaryTranslator():
    def __init__(self, word, part_of_speech, target_language):
        self.word = word
        self.part_of_speech = part_of_speech
        self.target_language = target_language
        self.meanings = []
        self._run()

    @staticmethod
    def _clean_heading(heading: str) -> str:
        return heading.strip().lower().replace('[edit]', '')

    def _run_url(self, url):
        r = requests.get(url)
        soup = bs4.BeautifulSoup(r.content, features='lxml')

        doc = Document(soup)
        doc.build_nodes_by_toc(self._clean_heading)
        heading = doc.find_heading([self.part_of_speech, 'translations'])
        section = doc.extract_section(heading)

        # Parse the translation sections into useful content
        for node in section.select('.NavFrame'):
            nav_head = node.select('.NavHead')[0]
            meaning = nav_head.find(text=True, recursive=False)
            for li in node.select('li'):
                text = li.get_text(strip=True)
                parts = text.split(':')
                language = parts[0].lower()
                translation = ':'.join(parts[1:])
                if language == self.target_language:
                    if translation:
                        self.meanings.append(Translation(meaning, translation))

        # We may not get useful content -- return the section of interest
        return section

    def _run(self):
        # Download the wiktionary page for this word
        section = self._run_url('https://en.wiktionary.org/wiki/%s' % self.word)
        if not self.meanings:
            # look for "see" and a link in the section
            for link in section.select('a'):
                if 'translation' in link.text.lower():
                    url = 'https://en.wiktionary.org'+link.get('href')
                    self._run_url(url)

    def __str__(self):
        return '%s:\n\t%s' % (
            self.word,
            '\n\t'.join(['%s' % m for m in self.meanings])
        )


def download_wikitionary_words_pos():
    # The word list is formatted as:
    # word, part-of-speech
    # Maybe I should make it a csv? But i was too lazy...
    with open('tools/most_common_words_wpos.txt') as f:
        lines = f.readlines()

    for line in lines:
        # skip words without a part of speech
        parts = line.strip().split(',')
        if len(parts) < 2:
            continue

        word = parts[0].strip().lower()
        pos = parts[1].strip().lower()
        print(word)
        try:
            t = WiktionaryTranslator(word, pos, 'korean')
        except Exception as e:
            print('Error with %s' % word)
            print(e)
        else:
            with open('tools/output_pos.txt', 'a', encoding="utf-8") as f:
                f.write('%s\n\n' % t)
        time.sleep(0.5)


if __name__ == '__main__':

    # aaah()
    '''
    # r = requests.get('https://en.wiktionary.org/wiki/dog')
    r = requests.get('https://en.wiktionary.org/wiki/small')
    soup = bs4.BeautifulSoup(r.content, features='lxml')
    doc = Document(soup)
    doc.build_nodes_by_toc(lambda h: h.strip().lower().replace('[edit]', ''))
    print('\n'.join(doc.get_toc_pretty()))
    # print('\n'.join(doc.get_toc()))
    # heading = doc.find_heading(['noun', 'translations'])
    heading = doc.find_heading(['adjective', 'translations'])
    print(heading)
    print(doc.extract_section(heading))
    '''

    # t = WiktionaryTranslator('book', 'noun', 'korean')
    # print(t)
    # t = WiktionaryTranslator('small', 'adjective', 'korean')
    # print(t)

    download_wikitionary_words_pos()

    # Wiktionary Seems to have more words than Bablenet...
    # t = BableTranslator('book', 'KO')
    # t = BableTranslator('small', 'KO')
    # t = Translator('small', 'Korean')
    # print(t)

    # t = Translator('small', 'Korean')
    # t = Translator('big', 'Korean')
    # t = Translator('dog', 'Korean')
    # print(t)
