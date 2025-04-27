import pandas as pd
from transformers import DistilBertTokenizer, TFDistilBertForSequenceClassification
from sklearn.model_selection import train_test_split
import tensorflow as tf

# Initialize tokenizer
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

# Load dataset
csv_file_path = 'balanced_XSS_dataset.csv'  # Ensure the path is correct
df = pd.read_csv(csv_file_path)

# Extract payloads and labels from the dataset
payloads = df['Sentence'].tolist()
labels = df['Label'].tolist()

# Split the dataset into training and testing sets
train_payloads, test_payloads, train_labels, test_labels = train_test_split(
    payloads, labels, test_size=0.2, random_state=42
)

# Tokenize training data
train_inputs = tokenizer(
    train_payloads,
    padding=True,
    truncation=True,
    max_length=256,
    return_tensors='tf'
)
train_labels = tf.convert_to_tensor(train_labels)

# Tokenize testing data
test_inputs = tokenizer(
    test_payloads,
    padding=True,
    truncation=True,
    max_length=256,
    return_tensors='tf'
)
test_labels = tf.convert_to_tensor(test_labels)

# Load the model
model = TFDistilBertForSequenceClassification.from_pretrained(
    'distilbert-base-uncased',
    num_labels=2  # 2 labels: malicious (1) and non-malicious (0)
)

# Prepare dataset function
def XSSDataset(inputs, labels, batch_size=16):
    dataset = tf.data.Dataset.from_tensor_slices(({
        'input_ids': inputs['input_ids'],
        'attention_mask': inputs['attention_mask']
    }, labels))
    dataset = dataset.shuffle(len(inputs['input_ids'])).batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return dataset

# Create TensorFlow datasets for training and testing
batch_size = 16
train_dataset = XSSDataset(train_inputs, train_labels, batch_size=batch_size)
test_dataset = XSSDataset(test_inputs, test_labels, batch_size=batch_size)

# Learning rate scheduler
lr_schedule = tf.keras.optimizers.schedules.ExponentialDecay(
    initial_learning_rate=3e-5,
    decay_steps=1000,
    decay_rate=0.96,
    staircase=True
)

# Define optimizer and loss
optimizer = tf.keras.optimizers.Adam(learning_rate=lr_schedule)
loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)

# Metrics
metrics = [tf.keras.metrics.SparseCategoricalAccuracy()]

# Compile the model
model.compile(optimizer=optimizer, loss=loss_fn, metrics=metrics)

# Train the model with validation
epochs = 3
history = model.fit(
    train_dataset,
    validation_data=test_dataset,
    epochs=epochs
)

# Save the fine-tuned model
model.save_pretrained('./03042025_XSS_Classification_fine_tuned_model')
tokenizer.save_pretrained('./03042025_XSS_Classification_fine_tuned_model')

print("Fine-tuning complete!")
