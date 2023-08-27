import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline


def run_preds(df: pd.DataFrame):
    X = df[["floor_size", "number_of_rooms"]].to_numpy()
    y = df["price"].to_numpy()

    # Step 2: Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)

    print(X_train.shape, y_train.shape)

    # Step 3: Model Training
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Step 4: Model Evaluation
    y_pred = model.predict(X_test)
    print(
        f"Root Mean Squared Error: {mean_squared_error(y_test, y_pred, squared=False)}"
    )
