#!/usr/bin/env python3
# right branching "parser"
# from  boilerplate code by Jon May (jonmay@isi.edu)
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
    from itertools import izip
else:
    izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit
from math import log
from collections import defaultdict
import copy



scriptdir = os.path.dirname(os.path.abspath(__file__))


reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
    if type(fh) is str:
        fh = open(fh, code)
        ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
        if sys.version_info[0] == 2:
            if code.startswith('r'):
                ret = reader(fh)
            elif code.startswith('w'):
                ret = writer(fh)
            else:
                sys.stderr.write("I didn't understand code "+code+"\n")
                sys.exit(1)
    return ret

def argmax_top(table):
    top =  table[0][-1]
    if top == []:
        return []
    if len(top) ==1:
        return top[0]
    max = 0
    for i in range(1,len(top)):
        if(top[i][1]>top[max][1]):
            max = i
    return top[max]

#transfer the sentence into seperate word
def to_word_list(sentence):
    word_list = sentence.split(" ")
    return word_list

#write a parsing and take the grammer and senctence as input, and output the highest_probability parse

def initial_table(sentence,children_list,parent,rule_prob):
    l = to_word_list(sentence)
    length = len(l)
    table = [[[] for i in range(length)] for i in range(length)] 
    for i in range(len(l)):
        if(l[i] in children_list.keys()):
            grammer_key = children_list[l[i]]
            for word in grammer_key:
                table[i][i].append( (parent[word][0],rule_prob[word]) )
        else:
            grammer_key = children_list["<unk>"]
            for word in grammer_key:
                table[i][i].append( (parent[word][0],rule_prob[word]) )
#     table_dict = {}
#     table_dict["table"] = table
#     table_dict["table_prob"] = table_prob
    return table

#use a funciton index_table it add a column to the original table in order to change index of it
def index_table(table):
    for l in table:
        l.insert(0,[])
    return table

def parsing_table(sentence,children_list,parent_list,grammer_prob):
    table_with_prob = initial_table(sentence,children_list,parent_list,grammer_prob)
    cky_table = index_table(table_with_prob)
    n = len(cky_table[0])
    for width in range(2,n):
        for start in range(0,n-width):
            end = start+width
            for mid in range(start+1,end):
                list_y = cky_table[start][mid]
                list_z = cky_table[mid][end]
                index_w = 0
                for index_y,y in enumerate(list_y):
                    for index_z,z in enumerate(list_z):
                        tag_y = y[0]
                        prob_y = y[1]
                        tag_z = z[0]
                        prob_z = z[1]
                        tag_x = tag_y + " " + tag_z
                        if(tag_x in children_list):
                            x_yz = children_list[tag_x]
                            for w in x_yz:
                                new_tag = parent_list[w][0]
                                prob_x = prob_y + prob_z + grammer_prob[w]
                                cky_table[start][end].append((new_tag,prob_x,start,mid,end,index_y,index_z,index_w))
                                index_w = index_w + 1
# index_z is the index of element in table[mid][end] table[mid][end] is a list 
# index_y is the index of element in table[start][mid],table [mid][end] is a list                          
    return cky_table

def backtrack(cky_table,i,j,k,sentence):
    if(j == i+1):
        return "("+cky_table[i][j][k][0] + " "+ sentence[i]+")"
    item = cky_table[i][j][k]
    new_tag=item[0]
    start1,end1 = item[2:4]
    start2,end2 = item[3:5]
    k1 = item[5]
    k2 = item[6]
    return '('+new_tag +' '+backtrack(cky_table,start1,end1,k1,sentence)+' '+backtrack(cky_table,start2,end2,k2,sentence)+')'

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
    ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
    group = parser.add_mutually_exclusive_group()
    dest = arg if dest is None else dest
    group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
    group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)

def main():
    parser = argparse.ArgumentParser(description="trivial right-branching parser that ignores any grammar passed in",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    addonoffarg(parser, 'debug', help="debug mode", default=False)
    parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input (one sentence per line strings) file")
    parser.add_argument("--grammarfile", "-g", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="grammar file; ignored")
    parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output (one tree per line) file")




    try:
        args = parser.parse_args()
    except IOError as msg:
        parser.error(str(msg))
    # workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))
    """
        def cleanwork():
            shutil.rmtree(workdir, ignore_errors=True)
        if args.debug:
            print(workdir)
        else:
            atexit.register(cleanwork)
    """
    grammer_dict = {}
    #file = open(args.grammarfile,'r')
    #file = args.grammarfile.open()
    #for line in file.readlines():
    for line in args.grammarfile:
        line=line.strip('\n')
        if(grammer_dict.has_key(line)):
            grammer_dict[line] = grammer_dict.get(line)+1
        else:
            grammer_dict[line] = 1
            
    count_sum = 0
    for key in grammer_dict.keys():
        count_sum = count_sum + grammer_dict.get(key)
    #count_sum is the total number of the rules
    grammer_freq=defaultdict(int)
    for key,value in grammer_dict.items():
        k = key.split(' -> ')[0]
        grammer_freq[k]+=value
    grammer_final={}
    
    for key,value in grammer_dict.items():
        k = key.split(' -> ')[0]
        grammer_final[key]=value*1.0/grammer_freq[k] 


    grammer_prob = copy.deepcopy(grammer_dict)

    for key in grammer_dict.keys():
        grammer_prob[key] = log(grammer_final[key],10)

    word_search_children = defaultdict(list)
    for k, v in grammer_prob.items():
        word_search_children[k.split("->")[-1].strip()].append(k)


    word_search_parent = defaultdict(list) 
    for k,v in grammer_prob.items():
        word_search_parent[k].append(k.split("->")[0].strip())
    
 
    for line in args.infile:
        line = line.strip('\n')
        word_list_q4 = to_word_list(line)
        table_q4 = parsing_table(line,word_search_children,word_search_parent,grammer_prob)
        best_top_q4 = argmax_top(table_q4)
        if(not best_top_q4 == []):
            q4_result = backtrack(table_q4,best_top_q4[2],best_top_q4[4],best_top_q4[-1],word_list_q4)
        else:
            q4_result = ""
        args.outfile.write(q4_result+'\n')


if __name__ == '__main__':
    main()
