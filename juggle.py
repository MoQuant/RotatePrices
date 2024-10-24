import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import websocket
import threading
import json

class Feed(threading.Thread):

    def __init__(self, tickers):
        threading.Thread.__init__(self)
        self.tickers = tickers
        self.prices = {}
        self.direction = {tick:None for tick in tickers}

    def run(self):
        conn = websocket.create_connection('wss://ws-feed.exchange.coinbase.com')
        msg = {'type':'subscribe','product_ids':self.tickers,'channels':['ticker']}
        conn.send(json.dumps(msg))
        while True:
            resp = json.loads(conn.recv())
            if 'type' in resp.keys():
                if resp['type'] == 'ticker':
                    ticker = resp['product_id']
                    price = float(resp['price'])
                    if ticker not in self.prices.keys():
                        self.prices[ticker] = []
                    self.prices[ticker].append(price)

                    if len(self.prices[ticker]) > 2:
                        self.direction[ticker] = 'High' if self.prices[ticker][-1] > self.prices[ticker][-2] else 'Low'
                        del self.prices[ticker][0]

    def synchronize(self):
        for i, j in self.direction.items():
            if j == None:
                return False
        return True

def rT(t):
    return np.sin(t)**2, np.sin(t)+np.cos(t), np.sin(t)*np.cos(t)

def curve(scale):
    T = np.arange(0, 2.0*np.pi+np.pi/32, np.pi/32)
    x, y, z = [], [], []
    for t in T:
        ux, uy, uz = rT(t)
        x.append(scale*ux)
        y.append(scale*uy)
        z.append(scale*uz)
    return [np.array(u) for u in (x, y, z)]

def sphere(scale):
    circle = lambda x, y: (np.sin(x)*np.cos(y), np.sin(x)*np.sin(y), np.cos(x))
    T = np.arange(0, 2.0*np.pi+np.pi/32, np.pi/32)
    x, y, z = [], [], []
    for ix in T:
        tx, ty, tz = [], [], []
        for jx in T:
            hx, hy, hz = circle(ix, jx)
            tx.append(scale*hx)
            ty.append(scale*hy)
            tz.append(scale*hz)
        x.append(tx)
        y.append(ty)
        z.append(tz)
    return [np.array(u) for u in (x, y, z)]


fig = plt.figure(figsize=(12, 7))
ax = fig.add_subplot(111, projection='3d')
fig.tight_layout()

cScale = 15

cx, cy, cz = curve(cScale)

tickers = ['ETH-USD','BTC-USD','USDT-USD','SOL-USD','ADA-USD']

client = Feed(tickers)
client.start()


F = [0, 1, 2, 3, 4]
S = [1.994, 3.3, 2.38, 1.4, 1.7]

while True:
    if client.synchronize() == True:
        for t in np.arange(0, 2*np.pi+np.pi/32, np.pi/32):
            ax.cla()
            for ii, (f, s) in enumerate(zip(F, S)):
                ax.plot(cx, cy, cz, color='black')
                sx, sy, sz = sphere(s)
                px, py, pz = rT(t + f)
                tick = tickers[ii]
                choice = client.direction[tick]
                if choice == 'High':
                    ax.plot_surface(cScale*px + sx, cScale*py + sy, cScale*pz + sz, color='limegreen')
                else:
                    ax.plot_surface(cScale*px + sx, cScale*py + sy, cScale*pz + sz, color='red')
                ax.text(cScale*px*1.2, cScale*py*1.2, cScale*pz*1.2, f'{tick} | {client.prices[tick][-1]}', color='black', fontsize=20)

            ax.grid(False)
            ax.axis('off')
            plt.pause(0.01)
    else:
        print('Tickers loaded: ', list(client.prices.keys()))
    
client.join()
plt.show()


