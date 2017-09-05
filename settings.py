DEBUG = False

# The maximum number of features to send to the projestions API if using the
# active layer geometry method
PROJESTIONS_MAX_FEATURES = 25

if DEBUG:
    PROJESTIONS_URL = 'http://localhost:3000/'
else:
    PROJESTIONS_URL = 'https://projest.io/ns/api/'
