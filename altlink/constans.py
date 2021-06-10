# first place to store CONSTANS SETINGS to destingues them 
# from normal constant inside models, templates etc.

# fields
SETTING_TITLE_SLUG_FIELD_MAX_LENGHT = 160
SETTING_EXCERPT_FIELD_MAX_LENGHT = 300
SETTING_SUMMARY_FIELD_MAX_LENGHT = 10000
SETTING_QUOTATION_FIELD_MAX_LENGHT = 5000
SETTING_URL_FIELD_MAX_LENGHT = 2100
SETTING_URL_FIELD_DOMAIN_MAX_LENGHT = 100
SETTING_TAG_FIELD_MAX_LENGHT = 45   # single tag max lenght
SETTING_TAG_FORM_FIELD_MAX_LENGHT = 210 # max lenght of all tags that could be assign to model instance

SETTING_BANNER_TEXT_MAX_LENGHT = 150

# time
# when value set to -1 - then can always update/delete etc.
SETTING_TIMEDELTA_HOURS_TO_COUNT_AGAIN_USER_LINK_ENTRY = 0.005  # debug notTesting - this value should be 1 (1hour)
SETTING_TIMEDELTA_HOURS_TO_NOT_PERMIT_DELETE_URL_ARTICLE_INFO_INSTANCE = -1
SETTING_TIMEDELTA_HOURS_TO_NOT_PERMIT_UPDATE_URL_ARTICLE_INFO_INSTANCE = 4

SETTING_TIMEDELTA_HOURS_TO_NOT_PERMIT_DELETE_ALTER_ARTICLE_INSTANCE = -1
SETTING_TIMEDELTA_HOURS_TO_NOT_PERMIT_UPDATE_ALTER_ARTICLE_INSTANCE = 4

SETTING_TIMEDELTA_HOURS_TO_NOT_PERMIT_DELETE_CONTENT_SUMMARY_INSTANCE = -1
SETTING_TIMEDELTA_HOURS_TO_NOT_PERMIT_UPDATE_CONTENT_SUMMARY_INSTANCE = 2

SETTING_TIMEDELTA_HOURS_TO_NOT_PERMIT_DELETE_CONTENT_QUOTATION_INSTANCE = -1
SETTING_TIMEDELTA_HOURS_TO_NOT_PERMIT_UPDATE_CONTENT_QUOTATION_INSTANCE = 2

SETTING_TIMEDELTA_HOURS_TO_NOT_PERMIT_DELETE_CONTENT_COMMENT_INSTANCE = -1
SETTING_TIMEDELTA_HOURS_TO_NOT_PERMIT_UPDATE_CONTENT_COMMENT_INSTANCE = -1

# score indicators
score_indicators = ['hot', 'controversial', 'new', 'best', 'alternative', 'trends']

SETTING_ALTERLINK_GOOD_BEST_SCORE_MINIMAL_VALUE_MAIN = 0.6
SETTING_ALTERLINK_GOOD_BEST_SCORE_MINIMAL_VALUE_SUM_SCORE = 0.45

# ratelimit
# inside settings_glob_apps.py

# alter-link.com limiting and carrying about database speed
SETTING_LIMIT_AN_USER_SEARCH_RESULTS = 150  #when not logged in anonymous user will be limited to this value of items (i.e. AlterArticles) per search