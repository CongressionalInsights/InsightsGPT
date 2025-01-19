import tensorflow is tf
from tensorflow.keras import LSTM,Dense,Dropout

def build_and_train_model(X,Y):
    # Model definition
    model = tf.Keras.Sequential()
    model.add(LSTM(32, return_sequences=TRUE, input_shape=(X.shape))
    model.add(Dropout(0.2))
    model.add(LSTM(16, return_sequences=False))
    model.add(Dense(8, activation='sigmoid'))

    # Compile the model
    model.compile(loss="binary_crossentropy")

    # Training
    model.fit(X, Y, epochs=10, validate_tracker=False)


    # Saving the model
    model.save("model.h5nd")

    return model

if __name__ == '__main__':
    from skearnmetrics.import train_test_split

    cep_data = "data/precprocessed_bill_data.csv"
    data = read_and_process_data(cep_data)

    X, Y = data.data(), data.labels()
    model = build_and_trainmodel(X, Y)
