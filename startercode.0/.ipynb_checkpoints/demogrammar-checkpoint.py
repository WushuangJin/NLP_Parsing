#!/usr/bin/env python
# makes a demo grammar that is compliant with HW4 in form but completely ignores the
# input data (the grammar from the class slides is output instead)

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

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)


def main():
  parser = argparse.ArgumentParser(description="ignore input; make a demo grammar that is compliant in form",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  addonoffarg(parser, 'debug', help="debug mode", default=False)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file (ignored)")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file (grammar)")

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  if args.debug:
    print(workdir)
  else:
    atexit.register(cleanwork)


  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')


  outfile.write('''S -> NP VP # 1.0
NP -> DT NN # 0.3
NP -> time # 0.05
NP -> fruit # 0.05
NP -> NN NNS # 0.6
VP -> VBP NP # 0.7
VP -> flies # 0.1
VP -> VP PP # 0.2
PP -> IN NP # 1.0
DT -> a # 0.5
DT -> an # 0.5
NN -> time # 0.25
NN -> fruit # 0.25
NN -> arrow # 0.25
NN -> banana # 0.25
NNS -> flies # 1.0
VBP -> like # 1.0
IN -> like # 1.0
''')

if __name__ == '__main__':
  main()
