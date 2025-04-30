# first trial
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
import pandas as pd
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import Counter


df = pd.read_csv('finalcomments.csv')

nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    text = text.lower()
    text = nltk.regexp_tokenize(text, r'\w+')
    text = [word for word in text if word not in stop_words]
    return ' '.join(text)

df['text'] = df['text'].apply(preprocess_text)



# second trial
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

nltk.download('stopwords')
nltk.download('punkt')  # Required for word_tokenize

stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    text = text.lower()
    text = word_tokenize(text)
    text = [word for word in text if word not in stop_words]
    return ' '.join(text)

df = pd.read_csv('finalcomments.csv')
df['text'] = df['text'].apply(preprocess_text)
vectorizer = TfidfVectorizer()
tfidf = vectorizer.fit_transform(df['text'])
word_freq = Counter(df['text'].str.split().explode().values)
most_repeated = word_freq.most_common(200)

print(most_repeated)



# third trial
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.util import ngrams
from nltk import pos_tag
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

nltk.download('stopwords')
nltk.download('punkt')  # Required for word_tokenize
nltk.download('averaged_perceptron_tagger')  # Required for POS tagging

stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    text = text.lower()
    tokens = word_tokenize(text)
    tagged_tokens = pos_tag(tokens)
    
    # Remove conjunctions, interjections, and articles
    filtered_tokens = [word for word, pos in tagged_tokens 
                         if pos not in ['CC', 'IN', 'UH', 'DT', 'TO', 'NN', 'NNS', 'NNP', 'NNPS',  # Nouns
                                     'RB', 'RBR', 'RBS',  # Adverbs
                                     'JJ', 'JJR', 'JJS']]
    
    # Extract bigrams (phrases)
    bigrams = list(ngrams(filtered_tokens, 2))
    
    # Convert bigrams to strings
    bigram_strings = [' '.join(bigram) for bigram in bigrams]
    
    return bigram_strings

df = pd.read_csv('finalcomments.csv')

# Apply preprocessing to each text sample
df['text'] = df['text'].apply(lambda x: ' '.join(preprocess_text(x)))

vectorizer = TfidfVectorizer()
tfidf = vectorizer.fit_transform(df['text'])

# Count the frequency of each bigram (phrase)
word_freq = Counter(df['text'].str.split().explode().values)

most_repeated = word_freq.most_common(2000)
print(most_repeated)




# finally worked
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.util import ngrams
from nltk import pos_tag
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer

nltk.download('stopwords')
nltk.download('punkt') 
nltk.download('averaged_perceptron_tagger') 

stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    text = text.lower()
    tokens = word_tokenize(text)
    tagged_tokens = pos_tag(tokens)
    
    filtered_tokens = [word for word, pos in tagged_tokens 
                         if pos not in ['CC', 'IN', 'UH', 'DT', 'TO']]
    bigrams = list(ngrams(filtered_tokens, 2))
    bigram_strings = [' '.join(bigram) for bigram in bigrams]
    return bigram_strings

df = pd.read_csv('finalcomments.csv')
df['text'] = df['text'].apply(lambda x: ' '.join(preprocess_text(x)))
vectorizer = TfidfVectorizer()
tfidf = vectorizer.fit_transform(df['text'])

word_freq = Counter(df['text'].str.split().explode().values)
most_repeated = word_freq.most_common(2000)

# Convert the result to a DataFrame
result_df = pd.DataFrame(most_repeated, columns=['Phrase', 'Frequency'])

# Print the result to a CSV file
result_df.to_csv('result.csv', index=False)



# a bit of adventure
# Preprocess comments
preprocessed_comments = [preprocess_comment(comment) for comment in comments]
# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(preprocessed_comments, labels, test_size=0.2, random_state=42)
# Create TF-IDF vectorizer
vectorizer = TfidfVectorizer()
# Fit vectorizer to training data and transform both training and testing data
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)
# Train Naive Bayes classifier on training data
clf = MultinomialNB()
clf.fit(X_train_tfidf, y_train)
# Evaluate classifier on testing data
accuracy = clf.score(X_test_tfidf, y_test)
print(f'Accuracy: {accuracy:.3f}')