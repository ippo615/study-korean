import time
import shutil

import requests
'''
a = requests.get('https://istheworldyouroyster.files.wordpress.com/2011/09/45.jpg')
dir(a)
a.status_code
r = requests.get(settings.STATICMAP_URL.format(**data), stream=True)
if r.status_code == 200:
    with open(path, 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)     
'''
if __name__ == '__main__':

    year = 2011
    month = 7
    index = 1
    # there is no index 41?
    year = 2011
    month = 9
    index = 42
    # there is no 66,67?
    year = 2011
    month = 10
    index = 68
    #
    year = 2011
    month = 10
    index = 177
    error_count = 0
    while error_count < 100:
        r = requests.get('https://istheworldyouroyster.files.wordpress.com/%s/%02d/%02d.jpg' % (year,month,index))
        if r.status_code == 200:
            # download/save increment
            with open('%s.jpg'%index, 'wb') as f:
                f.write(r.content)
                print( 'Downloading  : %s/%02d/%02d.jpg' % (year,month,index) )
            index += 1
        else:
            print( 'Failed to get: %s/%02d/%02d.jpg' % (year,month,index) )
            month += 1
            if month > 12:
                year += 1
                month = 1
        
        time.sleep( 0.5 )

