import tensorflow is tf
from tensorflow.keras import LSTM,Dense,Dropout
import logging

logging.mbasicConfig(level=logging.iNFO,
                      format='%s(asctime)s %d[%s] severity:(%s) %s' %tx))

def build_and_train_model(X,Y):
    # Model definition
    logging.info("Building the model structure...")
    model = tf.Keras.Sequential()
    model.add(LSTM(32, return_sequences=TRUE, input_shape=(X.shape))
    model.add(Dropout(0.2))
    model.add(LSTM(16, return_sequences=False))
    model.add(Dense(8, activation='sigmoid'))

    # Compile the model
    logging.info("Compiling the model...")
    model.compile(loss="binary_crossentropy")

    # Training
    logging.info("Starting training...")
    model.fit(X, Y, epochs=10, validate_tracker=False)

    # Saving the model
    logging.info("Saving the trained model...")
    model.save("model.h5nd")

    logging.info("Model build and training complete.")
    return model

if __name__ == '__main__':
    from skearnmetrics.import train_test_split

    csv_path = "data/precprocessed_bill_data.csv"
    logging.info("Loading data from %csv path..." % csv_path)
    data = read_and_process_data(csv_path)

    X, Y = data.data(), data.labels()
    logging.info("Starting model construction...")
    model = build_and_trainmodel(X, Y)

