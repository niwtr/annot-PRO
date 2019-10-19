#!/usr/bin/python
from __future__ import print_function
import re
import sys
try: input = raw_input
except NameError: pass

# TODO test python3 compatibility

class bcolors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

g_database = None
g_save_name = ''
g_default_backup_path = '/tmp/backup.txt'
g_feature_autosave = False
g_feature_debug = False
def save_data(take_input = True):
    global g_save_name
    if take_input:
        fname = input(bcolors.RED+'PATH TO SAVE (default: %s)> '\
                      % g_save_name+bcolors.END)
        g_save_name = g_save_name if fname == '' else fname
    try:
        with open(g_save_name, 'w') as outf:
            for data in g_database:
                outf.write('\t'.join(data) + '\n')
        print('Saved annotations.')
    except:
        with open(g_default_backup_path, 'w') as outf:
            for data in g_database:
                outf.write('\t'.join(data) + '\n')
        print('Something is wrong. I saved all data to %s.' % g_default_backup_path)

def print_help():
    print_available_extcmds()
    print_available_usercmds()
    print_available_fns()

def toggle_autosave():
    global g_feature_autosave
    g_feature_autosave = not g_feature_autosave
    print('Autosave: %s%s%s.' % (bcolors.RED, ('On' if g_feature_autosave else 'Off'), bcolors.END))
    if g_feature_autosave:
        print('The annotations will be saved at: %s' % g_save_name)


g_extcmds = {'quit': exit, 'Q':  exit, 'save': save_data, 's': save_data, 'help': print_help, 'h': print_help,
             'auto': toggle_autosave, 'autosave': toggle_autosave}
g_fndict = {'h': None, 's': 'SBAR', 'n': 'NP', 'p': 'PP', 'v': 'VP', 'a': 'ADJP', 'f': 'ADVP',}

    
def print_available_fns():
    global g_fndict
    print(bcolors.YELLOW+'Available syntax tags: '+bcolors.END)
    for (k, v) in g_fndict.items():
        print('%s -> %s' % (k,v))
    print()

    
def print_available_extcmds():
    global g_extcmds
    print(bcolors.YELLOW+'Available external commands: '+bcolors.END)
    for (k, v) in g_extcmds.items():
        print('%s -> %s' % (k,v))
    print()
def print_available_usercmds():
    print(bcolors.YELLOW+'Available user commands: '+bcolors.END)
    for (k, v) in {
            'rw': 'Rewrite original sentence.',
            '!': 'Mark current sample as bang.',
            'm': 'Annotate current sentence manually.',
            'p': 'Print current sample again.',
            'u': 'Move pointer to the last one (WARNING: will delete its annotation.)',
            'd': 'Move pointer to the next one (WARNING: will delete its annotation.)'
    }.items():
        print('%s -> %s' % (k,v))
    print()
    
    
print(bcolors.BOLD+'Welcome to COCO-RE Annotator!'+bcolors.END)
if len(sys.argv) != 2:
    print('Usage: python %s DATAFILE' % sys.argv[0])
    exit(1)

input_fname = sys.argv[1]
g_save_name = input_fname
with open(input_fname, 'r') as inf:
    g_database = list(map(lambda x: x.rstrip().split('\t'), inf.readlines()))

def print_raw_data(nth, rid, raw_ws):
    print((bcolors.BLUE+'[%d] ID: %s'+bcolors.END) % (nth, rid))
    print(' '.join(bcolors.UNDERLINE+w+bcolors.END for w in raw_ws))
    for nthw, ix in enumerate(raw_ws):
        print(nthw, end='')
        print(' ' * (len(raw_ws[nthw]) + 1 - len(str(nthw))), end='')
    print ()

cur_ix = 0
while cur_ix < len(g_database):
    print()
    raw_data = g_database[cur_ix]
    if len(raw_data) != 2:
        print(bcolors.YELLOW+'Skipped the [%d]-th sample.' % cur_ix + bcolors.END)
        cur_ix += 1
        continue
    raw_id = raw_data[0]
    raw = raw_data[1]
    raw_ws = raw.split(' ')
    print_raw_data(cur_ix, raw_id, raw_ws)
    annot = ''
    rewritn = False
    skip = False
    bang = False
    macro = False
    while annot == '':
        cmd = ''
        while cmd == '':
            cmd = input(bcolors.RED+('CONSOLE%s> ' % ('[AUTO]' if g_feature_autosave else ''))+bcolors.END)
        if cmd in g_extcmds:
            g_extcmds[cmd](); continue
        try:
            if cmd == 'rw':
                rw_raw = ''
                while rw_raw == '':
                    rw_raw = input(bcolors.YELLOW+'REWRITE> '+bcolors.END)
                raw_ws = rw_raw.split(' ')
                print_raw_data(cur_ix, raw_id, raw_ws)
                rewritn = True; continue
            elif cmd == '!':
                annot = cmd
            elif cmd == 'm':
                annot = input(bcolors.GREEN+'MANUAL> '+bcolors.END)
            elif cmd == 'p':
                print_raw_data(cur_ix, raw_id, raw_ws)
                continue
            elif cmd == 'u':
                cur_ix = max(0, cur_ix - 1)
                g_database[cur_ix] = g_database[cur_ix][:2]
                skip = True
            elif cmd == 'd':
                cur_ix = min(len(g_database) - 1, cur_ix + 1)
                g_database[cur_ix] = g_database[cur_ix][:2]
                skip = True
            else:
                if '!' in cmd:
                    bang = True
                    cmd = cmd.replace('!', '')

                # handle front/tail macro.
                if cmd[0].isupper():
                    cmd = '0h0' + cmd[0].lower() + cmd[1:]
                    macro = True
                if cmd[-1].isupper():
                    cmd = cmd[:-1] + str(len(raw_ws) - 1)+cmd[-1].lower()
                    macro = True
                mco_front = re.search('(\d+[A-Z])', cmd)
                if mco_front and mco_front.start() == 0:
                    hit = cmd[mco_front.start():mco_front.end()]
                    fn = hit[-1]; mv = hit[:-1]
                    cmd = '%sh%s%s' % (mv, mv, fn.lower()) + cmd[mco_front.end():]
                    macro = True
                if macro:
                    print(bcolors.YELLOW + ('Macro expand: %s' % cmd) + bcolors.END)

                cmds = re.split('(\d+)', cmd)[1:]
                fns = cmds[1::2]
                mvs = map(int, cmds[0:-1:2])
                if len(fns) > 0 and len(mvs) > 0 and len(fns) == len(mvs) and all(fn in g_fndict for fn in fns):
                    if fns[0] != 'h':
                        print('No any head word in annotation!'); continue
                    else:
                        hd = mvs[0] # head word index.
                        fns = fns[1:]; mvs = mvs[1:]
                    st = 0
                    for cr, fn in zip(mvs, fns):
                        blk = raw_ws[st:cr+1]
                        if hd in range(st, cr + 1):
                            blk.insert(hd - st, '*')
                        annot += (g_fndict[fn] + '(' + ' '.join(blk) + ')')
                        # print(annot)
                        st = cr + 1
                else:
                    print('Malformed command %s.' % cmd); continue
        except Exception:
            print('Illegal command: %s.' % cmd)
            if g_feature_debug:
                import traceback
                traceback.print_exc()
            annot='' ; continue
        if skip:
            break
        print(annot+('#' if rewritn else '') + ('!' if bang else ''))
        yon = input(bcolors.RED + 'Is this ok? [y]> '+bcolors.END)
        if yon != '' and yon != 'y':
            print('Rejected last annotation, try again.')
            annot = ''
        if annot != '':
            annot = annot if rewritn is False else annot + '#'
            annot = annot if bang is False else annot + '!'
    if not skip:
        raw_data.append(annot) # note the side effect.
        cur_ix += 1
        if g_feature_autosave:
            save_data(False)
save_data()

