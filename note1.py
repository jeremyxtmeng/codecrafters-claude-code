import argparse


# Creates a container object (named p) that holds instructions for 
# what command-line inputs your script should accept
p = argparse.ArgumentParser()

# Tells the parser to look for a flag named -p.
# required=True: script will stop and show an error if the user 
# runs the program without including -p and its value

p.add_argument("-k", required=True) # define the flag to watch for

# Scans the text typed in the terminal, 
# checks it against your rules, 
# and stores the resulting values inside a data object called args. 
# You can then access the input using args.p.

args = p.parse_args() # store all the flags

print(args.k) # watch for k flag