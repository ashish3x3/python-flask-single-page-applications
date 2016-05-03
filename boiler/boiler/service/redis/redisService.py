import redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)
r.set('foo','bar')
print r.get('foo')

"http://flask.pocoo.org/snippets/71/  check this url for a redis example service"

