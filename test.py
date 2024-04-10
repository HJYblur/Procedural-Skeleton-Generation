import csv
from skeleton_tree import skeleton_node_list


csv_file_path = './Test Data/test.csv'

with open(csv_file_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['name', 'weight', 'loss'])
    for node in skeleton_node_list:
        writer.writerow([node.name, 0, 0])
