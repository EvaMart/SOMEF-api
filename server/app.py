
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from somef.cli import run_cli
import os

app = FastAPI()


dict_filename = {
    "json": "metadata.json",
    "codemeta": "codemeta.json",
    "turtle": "graph.ttl"
}

@app.get('/')
def index():
    try:
        return FileResponse('static/index.html')
    except FileNotFoundError:
        return FileResponse('templates/index.html')


@app.get('/js/<path:filename>')
def serve_static_js(filename):
    return FileResponse(f'static/js/{filename}')


@app.get('/css/<path:filename>')
def serve_static_css(filename):
    return FileResponse(f'static/css/{filename}')


@app.get('/img/<path:filename>')
def serve_static_img(filename):
    return FileResponse(f'static/img/{filename}')


def extract_from_url(repo_url, threshold, ignore_classifiers):
    '''
    Extract metadata using GitHub repository URL as input to SOMEF
    '''
    if repo_url.find("https://github.com/") != 0:
        return "GitHub URL is not valid", 400

    path = './generated-files/'

    try:
        run_cli(threshold=threshold, ignore_classifiers=ignore_classifiers, repo_url=repo_url,
                output=path+dict_filename.get("json"),
                codemeta_out=path+dict_filename.get("codemeta"),
                graph_out=path+dict_filename.get("turtle"))

        return FileResponse(f'generated-files/{dict_filename.get("json")}')
    except Exception:
        return "Error extracting metadata from SOMEF", 500

def extract_from_content(content:str, threshold, ignore_classifiers):
    '''
    Extract metadata using readme content as input to SOMEF
    '''
    path = './generated-files/'

    # write the content to a file
    filepath = "./tmp/readme.txt"
    with open(filepath, "w") as f:
        f.write(content)
        
    try:
        # run SOMEF
        run_cli(threshold=threshold, ignore_classifiers=ignore_classifiers, doc_src=filepath,
                output=path+dict_filename.get("json"),
                codemeta_out=path+dict_filename.get("codemeta"),
                graph_out=path+dict_filename.get("turtle"))
        # remove the file
        os.remove(filepath)

        return FileResponse(f'generated-files/{dict_filename.get("json")}')
    except Exception as e:
        print(e)
        #return "Error extracting metadata from SOMEF", 500


class readme(BaseModel):
    content: str = None

@app.post('/metadata')
def get_metadata(threshold: float, ignore_classifiers: str, url: str = None, readme: readme = None):
    if threshold is None:
        return "Threshold is not Valid", 400

    ignore_classifiers = parse_ignore_classifiers(ignore_classifiers)
    if ignore_classifiers is None:
        return "Ignore Classifiers flag is not a boolean", 400

    # this endpoint accepts either a GitHub URL or a readme content to extract metadata

    # firts we check if a GitHub URL was provided
    repo_url = url
    if repo_url:
        # if so, we extract metadata from the URL
        extract_from_url(repo_url, threshold, ignore_classifiers)
    else:
        # if not, we check if a readme content was provided
        if readme.content is not None:
            print(readme.content)
            content = readme.content

            if content is not None:
                return extract_from_content(content, threshold, ignore_classifiers)
            else:
                return "GitHub URL or readme content were not provided", 400

        else:
            return "GitHub URL or readme content were not provided", 400
        

@app.get('/download')
def download_metadata(filetype):
    filename = dict_filename.get(filetype)
    if filename is None:
        return "Invalid file type for download", 400

    try:
        return FileResponse('generated-files', filename)
    except Exception:
        return "Requested file not found", 400


@app.get('/test')
def test():
    repo_url = 'https://github.com/KnowledgeCaptureAndDiscovery/somef'
    path = './generated-files/'
    run_cli(threshold=0.7, ignore_classifiers=False, repo_url=repo_url,
                    output=path+dict_filename.get("json"),
                    codemeta_out=path+dict_filename.get("codemeta"),
                    graph_out=path+dict_filename.get("turtle"))
    return FileResponse(f'generated-files/{dict_filename.get("turtle")}')


def parse_threshold(value):
    """Extract threshold value from the param for validation.
    :param value: Input threshold value.
    :return: A Float between 0 and 1, otherwise ``None``.
    """
    try:
        threshold = float(value)
        if 0 <= threshold <= 1:
            return threshold
    except Exception:
        return None

    return None


def parse_ignore_classifiers(value):
    """Extract flag ignore classifiers value from the param for validation.
    :param value: Input ignore_classifiers value.
    :return: A Boolean value [True, False], otherwise ``None``.
    """
    if value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        return None


if __name__ == '__main__':
    uvicorn.run("fastapi_code:app", host="0.0.0.0", port=5000, log_level="info")
