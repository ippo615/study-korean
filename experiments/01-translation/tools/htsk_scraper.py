
# Scraper for vocabulary on How to Study Korean
# https://www.howtostudykorean.com/

import requests
import bs4

if __name__ == '__main__':
    r = requests.get('https://www.howtostudykorean.com/unit1/unit-1-lessons-1-8/unit-1-lesson-1/')
    print(r.encoding)
    soup = bs4.BeautifulSoup(r.content, features='lxml')
    with open('a', 'w', encoding="utf-8") as f:
        # split by line? find lines that match {korean}={english}
        for b in soup.select('.play-button'):
            f.write(b)
    

