import subprocess
import sys
import glob
import os
import json
import time
from datetime import datetime
# import datefinder
from os import listdir
from os.path import isfile, join
import shutil

id_list = []
id_list2 = []
id_listUCSD = []


curr_dir = os.getcwd() + "/../data"
# print(curr_dir)

onlyfiles = [f for f in os.walk(curr_dir)]
# print(onlyfiles[2][2])

curr_dir = os.getcwd() + "/../data2"
# print(curr_dir)

onlyfiles2 = [f for f in os.walk(curr_dir)]

curr_dir = os.getcwd() + "/../dataUCSD"
# print(curr_dir)

onlyfilesUCSD = [f for f in os.walk(curr_dir)]

channel_names = ["event", "announcement", "bullet", "meet", "opportuni", "intern",
                 "week", "social", "info", "form", "link", "general", "advert", "seminar"]

cnt = 0
# for file_list in onlyfiles[1:]:
#     cnt+=1
#     for filename in file_list[2]:
#         filename_without_extension, extension = os.path.splitext(filename)
#         check_names = channel_names
#         # print(filename)
#         flag = False
#         if extension == ".json":
#             for name in check_names:
#                 if name in filename_without_extension:
#                     flag = True
#             if not flag:
#                 print(filename)
#                 print(filename_without_extension.split("[")[1][:-1])

# for file_list in onlyfiles2[1:]:
#     cnt+=1
#     for filename in file_list[2]:
#         filename_without_extension, extension = os.path.splitext(filename)
#         check_names = channel_names
#         # print(filename)
#         flag = False
#         if extension == ".json":
#             for name in check_names:
#                 if name in filename_without_extension:
#                     flag = True
#             if flag:
#                 print(filename)
#                 print(filename_without_extension.split("[")[1][:-1])
#                 id_list2.append(filename_without_extension.split("[")[1][:-1])
# print(id_list2)

extract_array = os.listdir(curr_dir)
data_folder_name = '/home/ec2-user/scraper/dataUCSD/'

for folder_name in extract_array:

    for dirname, dirs, files in os.walk(data_folder_name+folder_name):
        for file_id, filename in enumerate(files):

            filename_without_extension, extension = os.path.splitext(filename)
            check_names = channel_names
            # print(filename)
            flag = False
            if extension == ".json":
                for name in check_names:
                    if name in filename_without_extension.lower():
                        flag = True
                if not flag:
                    print(dirname+"/"+filename)
                    os.remove(dirname+"/"+filename)
                    # file_name_space = file_list[0]+"/"+filename_without_extension
                    # try:
                    #     os.remove(file_name_space)
                    #     print(file_name_space, "removed")
                    # except:
                    #     print("ERROR")
                    cnt += 1
print(cnt)
