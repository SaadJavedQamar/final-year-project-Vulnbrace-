import pandas as pd
from transformers import DistilBertTokenizer, TFDistilBertForSequenceClassification
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import tensorflow as tf
import matplotlib.pyplot as plt

# Initialize tokenizer
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')

# Load dataset
csv_file_path = 'balanced_SQL_dataset.csv'
df = pd.read_csv(csv_file_path)

# Extract payloads and labels from the dataset
payloads = df['Query'].tolist()
labels = df['Label'].tolist()

# Stratified split for balanced data
train_payloads, test_payloads, train_labels, test_labels = train_test_split(
    payloads, labels, test_size=0.3, random_state=42, stratify=labels
)

# Tokenize training data
train_inputs = tokenizer(
    train_payloads,
    padding=True,
    truncation=True,
    max_length=512,
    return_tensors='tf'
)
train_labels = tf.convert_to_tensor(train_labels)

# Tokenize testing data
test_inputs = tokenizer(
    test_payloads,
    padding=True,
    truncation=True,
    max_length=512,
    return_tensors='tf'
)
test_labels = tf.convert_to_tensor(test_labels)

# Load the model
model = TFDistilBertForSequenceClassification.from_pretrained(
    'distilbert-base-uncased',
    num_labels=2  # 2 labels: malicious (1) and non-malicious (0)
)

# Freeze lower layers to reduce overfitting
for layer in model.distilbert.transformer.layer[:-2]:
    layer.trainable = False

# Apply L2 regularization to the classifier layer
regularizer = tf.keras.regularizers.L2(0.01)
model.classifier.add_loss(lambda: regularizer(model.classifier.kernel))

# Prepare dataset function
def SQLDataset(inputs, labels, batch_size=16):
    dataset = tf.data.Dataset.from_tensor_slices(({
        'input_ids': inputs['input_ids'],
        'attention_mask': inputs['attention_mask']
    }, labels))
    dataset = dataset.shuffle(len(inputs['input_ids'])).batch(batch_size).prefetch(tf.data.AUTOTUNE)
    return dataset

# Create TensorFlow datasets for training and testing
batch_size = 16
train_dataset = SQLDataset(train_inputs, train_labels, batch_size=batch_size)
test_dataset = SQLDataset(test_inputs, test_labels, batch_size=batch_size)

# Learning rate scheduler with warm-up
lr_schedule = tf.keras.optimizers.schedules.PolynomialDecay(
    initial_learning_rate=1e-6,  # Start small
    end_learning_rate=1e-5,
    decay_steps=10000,
    power=1.0
)

# Define optimizer with gradient clipping
optimizer = tf.keras.optimizers.Adam(learning_rate=lr_schedule, clipnorm=1.0)

# Loss function with label smoothing
loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)

# Metrics
metrics = [tf.keras.metrics.SparseCategoricalAccuracy()]

# Compile the model
model.compile(optimizer=optimizer, loss=loss_fn, metrics=metrics)

# Early Stopping Callback
early_stopping = tf.keras.callbacks.EarlyStopping(
    monitor='val_loss',
    patience=3,  # Allow more fluctuation
    restore_best_weights=True
)

# Train the model with validation and early stopping
epochs = 5
history = model.fit(
    train_dataset,
    validation_data=test_dataset,
    epochs=epochs,
    callbacks=[early_stopping]
)

# Save the fine-tuned model
model.save_pretrained('./DistilBERT_fine_tuned_model')
tokenizer.save_pretrained('./DistilBERT_fine_tuned_model')

# Evaluate and print classification metrics
preds = model.predict(test_dataset)
predicted_labels = tf.argmax(preds.logits, axis=-1).numpy()
print(classification_report(test_labels.numpy(), predicted_labels))

print("Fine-tuning complete!")

plt.plot(history.history['sparse_categorical_accuracy'], label='Training Accuracy')
plt.plot(history.history['val_sparse_categorical_accuracy'], label='Validation Accuracy')
plt.title('Model Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

# Plot loss
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Model Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()