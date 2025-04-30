# import libraries
import praw
import pandas as pd
from praw.models import MoreComments

# input authentication
reddit = praw.Reddit(
    client_id='',
    client_secret='',
    user_agent=''
)

url = "https://www.reddit.com/r/AskReddit/comments/1gtu1fe/whats_a_scam_that_youre_surprised_people_still/"
post = reddit.submission(url=url)
print(post.title)

comment_ids = []
comment_bodies = []

def get_comments(comments):
    for comment in comments:
        if isinstance(comment, MoreComments):
            get_comments(comment.comments())
        else:
            comment_ids.append(comment.id)
            comment_bodies.append(comment.body)
            if comment.replies:
                get_comments(comment.replies)

get_comments(post.comments)

df = pd.DataFrame({
    'Comment ID': comment_ids,
    'Comment Body': comment_bodies
})

df.to_csv('comments.csv', index=False)
# except praw.exceptions.APIException as e:
#     print(f"API error: {e}")
# except Exception as e:
#     print(f"Error: {e}")