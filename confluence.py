import getpass
import requests
import json

class ConfluenceUpdater:
    '''
    This is a Confluence wrapper that manages page updates and allows the
    manipulation of attachments.
    '''
    def __init__(self, auth, baseurl):
        import mimetypes
        import requests
        import json
        import os

        '''
        Args:
            auth (tuple(string, string)): Tuple that contains the username and
                password for the Confluence server.
            baseurl (string): The URL of the server. Typically ends with
                rest/api/content.
        '''
        self.auth = auth
        self.baseurl = baseurl
        self.session = requests.Session()
        self.session.auth = self.auth

    def page_ancestors_get(self, pageId):
        '''
        Gets the ancestor of the provided pageId.

        Args:
            pageId (str): Usually numbers, found by going into a page in edit
                mode and getting it from the URL's draftId.

        Returns:
            string: The page's ancestors.
        '''
        url = '{base}/{pageId}?expand=ancestors'.format(
            base = self.baseurl,
            pageId = str(pageId))

        r = self.session.get(url)

        r.raise_for_status()

        return r.json()['ancestors']

    def page_get(self, pageId):
        '''
        Gets the pageId's content.

        Args:
            pageId (str): The confluence page ID to get.

        Returns:
            dict: The page's content
        '''
        url = '{base}/{pageId}?expand=space,body.storage,version'.format(
            base = self.baseurl,
            pageId = str(pageId))

        r = self.session.get(url)

        r.raise_for_status()

        page = r.json()

        return page

    def page_update(self, body, pageId, append = True, wiki = False):
        '''
        Appends new content to the page, optionally overwriting everything.

        Args:
            body (str): Data to put on the page.
            pageId (str): Page ID to update.
            append (bool): Appends if True, overwrites if False. Default: True.
        '''
        
        if wiki:
            wiki = 'wiki'
        else:
            wiki = 'storage'
            
        pageId = str(pageId)
        
        url = '{base}/{pageId}'.format(
            base = self.baseurl,
            pageId = pageId)

        anc = self.page_ancestors_get(pageId)[-1]

        page = self.page_get(pageId)

        data = {
            'id' : pageId,
            'type' : 'page',
            'title' : page['title'],
            'version' : {'number' : page['version']['number'] + 1},
            'ancestors' : [anc],
            'body' : {
                'storage' : {
                    'representation' : wiki,
                    'value' : ''
                }
            }
        }

        dataValue = ''
        if append:
            dataValue = page['body']['storage']['value'] + body
        else:
            dataValue = body

        data['body']['storage']['value'] = dataValue

        data = json.dumps(data)
            
        r = self.session.put(url,
                         data = data,
                         headers = { 'Content-Type' : 'application/json' })

        r.raise_for_status()

    def attachment_get(self, pageId):
        '''
        Gets all the attachments from a page.

        Args:
            pageId (str): Confluence page ID.

        Returns:
            list(str): A list of all the attachments that are on the page.
        '''
        url = '{}/{}/child/attachment/'.format(self.baseurl, str(pageId))

        r = requests.get(url, auth = self.auth)

        r.raise_for_status()

        res = r.json()

        titles = []
        for r in res['results']:
            if r['type'] == 'attachment':
                titles.append(r['title'])

        return titles

    def attachment_upload(self, pathToFile, targetFileName, pageId):
        '''
        Uploads an attachment to a page.

        Args:
            pathToFile (str): File to upload.
            targetFileName (str): Name on the Confluence page.
            pageId (str): Confluence page ID.
        '''
        pageId = str(pageId)
        
        url = '{}/{}/child/attachment/'.format(self.baseurl, pageId)
        headers = {'X-Atlassian-Token':'no-check'}

        content_type, _ = mimetypes.guess_type(os.path.split(pathToFile)[1])
        if content_type is None:
            content_type = 'image/png'

        with open(pathToFile, 'rb') as fileBytes:
            files = {'file':(targetFileName, fileBytes, content_type)}
            r = requests.post(url,
                              headers = headers,
                              files = files,
                              auth = self.auth)

        r.raise_for_status()

        return '{}/download/attachments/{}/{}'.format(
            self.baseurl[:self.baseurl.find('/rest/api/content')],
            pageId,
            targetFileName)
