import pandas as pd
import numpy as np
import os, glob
import cv2
import time
from Customer import Customer
from Supermarket import Supermarket
from tiles_skeleton import SupermarketMap, MARKET

def create_unique_customer_id(row):
    return row['timestamp'].dayofyear * 100000 + row['customer_no']

def create_dataframe():
    df = pd.concat(map(lambda f: pd.read_csv(f, delimiter=';'),glob.glob('data/*.csv')))
    df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S")
    df['hour']= df['timestamp'].dt.hour
    df['minute'] = df['timestamp'].dt.minute
    df['weekday'] = df['timestamp'].dt.day_name()
    df['customer_id'] = df.apply(lambda row: create_unique_customer_id(row), axis=1)
    df = df.drop(['customer_no'], axis = 1)
    return df

def create_transition_matrix(df):
    trans = df.groupby(['customer_id', 'timestamp', 'location']).all().reset_index()
    trans['after'] = trans.groupby('customer_id')['location'].shift(-1)
    trans = trans.rename(columns={'location':'before'})
    trans = trans.drop(['customer_id','timestamp','hour','minute','weekday'], axis=1)
    trans = trans.fillna('checkout')
    matrix = pd.crosstab(trans['before'], trans['after'], normalize=0)
    return matrix

def show_animation(df, matrix):
    background = np.zeros((700, 1000, 3), np.uint8)
    tiles = cv2.imread("tiles.png")

    market = SupermarketMap(MARKET, tiles)
    c = Customer(df.at[0,'customer_id'], df.at[0,'location'], matrix, market, market.tiles[3*32 : 4* 32, 0 : 32])
 
    while True:
        time.sleep(2)
        frame = background.copy()
        market.draw(frame)
        c.draw(frame)
        c.next_state()
        cv2.imshow("frame", frame)

        key = chr(cv2.waitKey(1) & 0xFF)
        if key == "q":
            break

    cv2.destroyAllWindows()

    market.write_image("supermarket.png")


if __name__ == "__main__":
    df = create_dataframe()
    matrix = create_transition_matrix(df)
    df = df.reset_index()

    df_cos = df.groupby(['customer_id',]).first().reset_index()


    show_animation(df_cos, matrix)

    #customers = []
    #for i in range(0,3):
    #    customers.append(Customer(df_cos.at[i,'customer_id'], df_cos.at[i,'location'], matrix))

    #smarket = Supermarket(customers)
    #print(smarket)
    #while smarket.is_active():
    #    smarket.next_minute()
    #    print(smarket)
