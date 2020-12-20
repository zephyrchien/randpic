#!/usr/bin/env python3
# coding:utf-8
import io
import uuid
import flask
import utils
import config
import threading

app = flask.Flask(__name__)
cache = utils.ImgCache(config.URL,config.CACE_SIZE)
history = utils.History(config.LIFETIME)
t = threading.Thread(target=cache.crontab,args=(config.FETCH_THREADS,config.FETCH_INTERVAL))

@app.route(config.PATH)
def api():
    url = cache.get()
    if not url:
        return flask.abort(404)
    resp = utils.secure_get(url)
    if not resp:
        return flask.abort(404)
    id = uuid.uuid4().hex
    history.set(id,url)
    wresp = flask.make_response(flask.send_file(io.BytesIO(resp.content),mimetype='image/jpeg'))
    wresp.set_cookie('id',id,path=config.MANUAL_PATH,secure=True)
    return wresp

@app.route(config.MANUAL_PATH)
def manual():
    req = flask.request
    if not req.json:
        return 404
    cmd = req.json.get('cmd')
    if cmd not in ['netx','previous']:
        return 404
    id = req.request.cookies.get('id')
    if not id:
        return api()
    current_url = history.get(id)
    if not current_url:
        return api()
    new_url = utils.get_new_url(cmd,current_url)
    resp = utils.secure_get(new_url)
    if not resp:
        return flask.abort(404)
    if resp.status_code != 200:
        return api()
    history.set(id,new_url)
    wresp = flask.make_response(flask.send_file(io.BytesIO(resp.content),mimetype='image/jpeg'))
    return wresp

if __name__ == '__main__':
    t.start()
    app.run(host=config.HOST, port=config.PORT, debug=False)
