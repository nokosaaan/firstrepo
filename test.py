import json
import numpy as np
import random

def main():
    f = open("data.json", 'r')

    json_data = json.load(f)

    #game = ["chunithm"]
    num_list = []
    for i in range(len(json_data)):
        s = '"'+format(i)+'"'
        num_list.append(s)
        #print(num_list[i])
    u=[]
    #x=[]
    #y=[]
    #z=[]
    for v in json_data.values():
        #print(v['name'],end="\t")
        #print(v['diff'])
        if v['diff']=="11":
            u.append(v['name'])
        for i in range(len(v['data'])):
            print("{}".format(v['data'][i]),end="\t")
        #print("\n")
    print(u)
    answer = random.choice(u)
    print(answer)
    '''
    for i in range(10):
        print('"%d"'%i)
    
    for i in range(len(json_data[game[0]])):
        print("{0:8s} 曲名:{1} 難易度:{2} 情報: ".format(game[0],json_data[game[0]][num_list[i]]["name"],json_data[game[0]][num_list[i]]["diff"]),end="\t")
        for j in range(len(json_data[game[0]][num_list[i]]["data"])):
            print("{}".format(json_data[game[0]][num_list[i]]["data"][j]),end="\n")
        print()
    '''

if __name__=='__main__':
    main()