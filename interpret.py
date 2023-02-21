##
#   IPP projekt: cast 2 - interpret.py
#   Autor: Dominik Horky
#   VUT FIT, 2021
#
##

##
#   NAVRATOVE KODY
#   [viz interpret_exit(exit_value, ...)]
#
#   keyword-string      kod             poznamka
#
#   'args'              10              argparse, --source/--input
#   'input'             11              fopen --source / --input
#   'output'            12              vystup
#   'XMLformat'         31              well-formatted
#   'XMLstruct'         32              chyby ve strukture XML, syntax, lexical, neco i ze semantiky, ...
#   'lexical'           32              lexikalni chyby pri kontrolach struktury XML
#   'semantic'          52              nedefinovane navesti, redefinice promenne
#   'operand_type'      53              spatny typ operandu
#   'no_variable'       54              pristup k neexistujici promenne (v ramci ktery EXISTUJE)
#   'no_frame'          55              pristup do neexistujiciho ramce
#   'missing_value'     56              chybi hodnota v datovem zasobniku, call zasobniku, v promenne
#   'bad_value'         57              deleni 0, spatna navratova hodnota EXIT, ..
#   'string_error'      58              spatna prace se stringem
#   'internal'          99              zadani, ostatni vnitrni chyby kodu tohoto skriptu, ..
#   -                   101             zadost uzivatele (-rs)
#   -neuvedeno-         -neuvedeno-     pri neuvedem stringu (viz vyse) ci spatnem/neplatnem navratovem kodu pri volani 'interpret_exit' [aka chyba implementace skriptu 'interpret.py']
##

###
### DEFs
###


###
### INTERNI

## prelozi text argparse do cestiny ##
def convertArgparseMessages(s):
    subDict = \
    {'usage: ':'pouziti: ',
    'expected one argument':'ocekavan jeden argument',
    'optional arguments':'nepovinne argumenty',
    'show this help message and exit':'vypise tuto zpravu a ukonci skript',
    'unrecognized arguments: %s':'nezname argumenty: %s',
    '%(prog)s: error: %(message)s\n': '%(prog)s: chyba: %(message)s\n',}
    if s in subDict:
        s = subDict[s]
    return s

## pomocna funkce pro interpret_exit(...), zpracuje exit_code (at uz se jedna o cislo nebo string) ##
def exit_convert(exit_code):
    valid_exits = [10, 11, 12, 31, 32, 52, 53, 54, 55, 56, 57, 58, 99, 32, 101]
    exit_number = 0
    try:
        exit_number = int(exit_code)
    except ValueError:
        exit_strings = ['args', 'input', 'output', 'XMLformat', 'XMLstruct', 'semantic', 'operand_type', 'no_variable', 'no_frame', 'missing_value', 'bad_value', 'string_error', 'internal', 'lexical']
        for string in exit_strings:
            if string == exit_code:
                return valid_exits[exit_number]
            else:
                exit_number = exit_number + 1
    
    for valid in valid_exits:
        if exit_number == valid:
            return exit_number
    
    print('[!!] Neocekavana nebo neosetrena chyba. (pravdepodobne spatny string ci navratovy kod v internim kodu [\'interpret.py\'])', file=sys.stderr)
    return exit_number  # vraci 13 (protoze validnich exit kodu je 12, viz. implementace vyse) nebo jakoukoli jinou nesmyslnou hodnotu

## ukonci interpret.py s chybovou hlaskou na stderr a prislusnym navratovym kodem ##
def interpret_exit(exit_code={'args', 'input', 'output', 'XMLformat', 'XMLstruct', 'semantic', 'operand_type', 'no_variable', 'no_frame', 'missing_value', 'bad_value', 'string_error', 'internal', 'lexical', 10, 11, 12, 31, 32, 52, 53, 54, 55, 56, 57, 58, 99, 101}, string=None):
    if (string == None):
        string = 'neznama chyba (ci chybejici popis chyby)'
    if (exit_code == 'internal') or exit_code == 99:
        beg_msg = 'Interni chyba skriptu: '
    elif exit_code == 101:
        beg_msg = '[-rs]: '
    else:
        beg_msg = 'Chyba: '
    print(beg_msg + string, file=sys.stderr)
    exit(exit_convert(exit_code))

## vypis informaci o prubehu skriptu pri zapnutem '-v' nebo '--verbose' flagu ##
def verbose_print(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)

## prida instrukci do seznamu, vyzadovano jeji jmeno, poradi a pocet argumentu (ve vstupu) ##
def instr_add(instr_name, instr_order, instr_arg_cnt=-1):
    global PROG_INSTR
    instr_data = [instr_name.upper(), int(instr_order), int(instr_arg_cnt)]
    arg_data = [int(instr_order), "", "", "", "", "", ""]
    PROG_INSTR.insert(int(instr_order)-1, instr_data)
    PROG_ARGS.insert(int(instr_order)-1, arg_data)
    
## odebere instrukci ze seznamu, vyzadovano jeji poradi, nepovinne jeji nazev a pocet argumentu (pouze pro zrychleni) ##
def instr_remove(instr_order, instr_name=None, instr_arg_cnt=None):
    global PROG_INSTR
    if (instr_name == None) or (instr_arg_cnt == None):
        for instruction in PROG_INSTR:
            if instruction[1] == instr_order:
                instr_name = instruction[0]
                instr_arg_cnt = instruction[2]
        if (instr_name == None):
            interpret_exit('internal', 'instr_remove: na danem poradi (' + str(instr_order) +') zadna instrukce neexistuje')

    PROG_INSTR.remove([instr_name, int(instr_order), int(instr_arg_cnt)])

## zmeni hodnotu argcnt instrukce na danem indexu  ##
def instr_modify_argcnt(index, value):
    global PROG_INSTR
    if value < 0 or value > 3:
        interpret_exit('internal', 'instr_modify_argcnt: neplatna hodnota argcnt [povoleno: 0-3 (int)]')
    i = 0
    for instruction in PROG_INSTR:
        if i == index:
            instruction[2] = value
            return
        i = i + 1

    interpret_exit('internal', 'instr_modify_argcnt: instrukce na danem poradi (' + str(order) + ') neexistuje')

## najde instrukci na danem poradi a vrati jeji index v poli PROG_INSTR nebo -1 pokud nebyla nalezena ##
def instr_find(order):
    i = 0
    for instruction in PROG_INSTR:
        if order == instruction[1]:
            return i
        i = i + 1
    return -1

## vrati nazev instrukce na danem poradi ##
def instr_getname(order):
    index = instr_find(order)
    if index < 0:
        interpret_exit('internal', 'instr_getname: instrukce na danem poradi (' + str(order) + ') neexistuje')
    return PROG_INSTR[index][0]

## vrati pocet zjistenych argumentu instrukce ##
def instr_getargcnt(order):
    index = instr_find(order)
    if index < 0:
        interpret_exit('internal', 'instr_getname: instrukce na danem poradi (' + str(order) + ') neexistuje')
    return PROG_INSTR[index][2]

## zkontroluje, zda poradi vsech instrukci je validni a zda se jedna o uplny seznam instrukci
def instr_list_valid():
    global PROG_ARGS
    global PROG_INSTR
    global PROG_LABELS
    global PROC_CALLS
    for element in PROG_INSTR:
        same = 0
        for element_2 in PROG_INSTR:
            if element[1] == element_2[1]:
                same = same + 1
        if same != 1:
            interpret_exit('XMLstruct', 'poradi instrukci neni jedinecne')
    verbose_print('Kontrola poradi instrukci OK')
    i = 1
    for element in PROG_INSTR:
        element[1] = i
        i = i + 1

    for k in range(0, 1):
        i = 0
        for argument in PROG_ARGS:
            j = 0
            lowest = argument
            for arg2 in PROG_ARGS:
                if arg2[0] < argument[0] and i < j and lowest[0] > arg2[0]:
                    lowest = arg2
                    lowest_index = j
                j = j + 1
            if lowest != argument:
                tmp = PROG_ARGS[i]
                PROG_ARGS[i] = lowest 
                PROG_ARGS[lowest_index] = tmp
            i = i + 1

    i = 1
    for element in PROG_ARGS:
        element[0] = i
        i = i + 1
    
    i = 0
    for element in PROG_LABELS:
        for instr in PROG_INSTR:
            if instr[0] == 'LABEL':
                ind = instr[1]-1
                if PROG_ARGS[ind][1] == element[0]:
                    element[1] = PROG_ARGS[ind][0]
        i = i + 1

    i = 0
    for element in PROG_CALLS:
        for label in PROG_INSTR:
            if label[0] == 'CALL' and PROG_ARGS[i][1] == element[0]:
                element[0] = PROG_ARGS[i][1]
        i = i + 1


## nastavi hodnotu daneho argumentu v seznamu, vyzadovano poradi instrukce ke ktere argument patri, poradi argumentu a hodnota a typ ##
def arg_set(instr_order, arg_num, value, arg_type):
    global PROG_ARGS
    index = arg_find(instr_order)
    if index < 0:
        interpret_exit('internal', 'arg_set: argumenty pro instrukci na pozici \'' + instr_order +'\' nenalezeny')
    arg_list = PROG_ARGS[index]
    arg_list[arg_num] = value
    arg_list[arg_num+3] = arg_type
    
## najde v poli argumentu dany seznam argumentu pro instrukci, vrati index v poli nebo -1 pokud neexistuje ##    
def arg_find(instr_order):
    i = 0
    for argument in PROG_ARGS:
        if argument[0] == instr_order:
            return i
        i = i + 1
    return -1

## vrat v seznamu argumentu (v poli argumentu) dany argument ##
def arg_get(arglist, argnum):
    if argnum < 0 or argnum > 6:
        interpret_exit('internal', 'arg_get: mimo meze seznamu')
    return arglist[argnum]

## overi, zda argumenty instrukce na danem poradi byly zapsany do seznamu (z XML zdroje - ve spravnem poctu) ##
def arg_check(instr_order, arg_nums):
    index = arg_find(instr_order)
    if index < 0:
        interpret_exit('internal', 'arg_exists: pro instrukci na pozici \'' + instr_order +'\' nenalezeny')
    
    name = instr_getname(instr_order)
    instr_index = 0
    i = 0
    for names in INSTR_LIST:
        if name == names:
            instr_index = i
        i = i + 1

    if instr_index >= 0 and instr_index <= 4:
        if arg_nums != 0:
            interpret_exit(32, 'nespravny pocet operandu-argumentu instrukce '+str(instr_order))
    elif instr_index >= 5 and instr_index <= 13:
        if arg_nums != 1 or PROG_ARGS[index][1] == '':
            interpret_exit(32, 'nespravny pocet operandu-argumentu instrukce '+str(instr_order))
    elif instr_index >= 14 and instr_index <= 19:
        if arg_nums != 2 or PROG_ARGS[index][1] == '' or PROG_ARGS[index][2] == '':
            interpret_exit(32, 'nespravny pocet operandu-argumentu instrukce '+str(instr_order))
    else:
        if arg_nums != 3 or PROG_ARGS[index][1] == '' or PROG_ARGS[index][2] == '' or PROG_ARGS[index][3] == '':
            interpret_exit(32, 'nespravny pocet operandu-argumentu instrukce '+str(instr_order))
    verbose_print('[SLS:' + str(instr_order) + '] Pocet argumentu v instrukci OK')
    arg_check_type(instr_order)

## zkontroluje spravne typy argumentu instrukce na dane pozici ##
def arg_check_type(instr_order):
    arg_index = arg_find(instr_order)
    if arg_index < 0:
        interpret_exit('internal', 'arg_exists: pro instrukci na pozici \'' + instr_order +'\' nenalezeny')
    arg_list = PROG_ARGS[arg_index]

    instr_name = instr_getname(instr_order)
    count = 0
    index = 0
    for instruction in INSTR_LIST:
        if instruction == instr_name:
            index = count
        count = count + 1
    
    arg_cnt_right = arg_check_type_switch(index)
    if arg_cnt_right != instr_getargcnt(instr_order):
        interpret_exit('XMLstruct', 'nespravny pocet parametru instrukce na pozici \'' + str(instr_order) +'\' (parametru: ' + str(instr_getargcnt(instr_order)) + ', ocekavano: ' + str(arg_cnt_right) + ')')
    
    for i in range(1, arg_cnt_right+1):
        argument_value = arg_get(arg_list, i)
        arg_check_type_value(index, instr_order, argument_value, i)
        verbose_print('\t analyza ' + str(i) + '. argumentu OK')

## zkontroloje spravny typ argumentu ##
def arg_check_type_value(instr_pos, instr_order, arg_val, arg_pos):
    if arg_pos == 1:
        if ( instr_pos >= 5 and instr_pos <= 6 ) or ( instr_pos >= 14 and instr_pos <= 32 ):
            var_regex_check(arg_val)
            var_add(arg_val, instr_order)
        elif ( instr_pos >= 7 and instr_pos <= 9 ) or ( instr_pos >= 33 and instr_pos <= 34 ):
            label_regex_check(arg_val)
        elif ( instr_pos >= 10 and instr_pos <= 13 ):
            sym_regex_check(arg_val)
            sym_typecheck(instr_order, arg_val, arg_pos)
        else:
            interpret_exit('operand_type', 'neocekavany typ argumentu na prvni pozici instrukce cislo ' + str(instr_order))
    elif arg_pos == 2:
        if ( instr_pos >= 14 and instr_pos <= 18 ) or ( instr_pos >= 20 and instr_pos <= 34 ):
            sym_regex_check(arg_val)
            sym_typecheck(instr_order, arg_val, arg_pos)
        elif ( instr_pos == 19 ):
            type_regex_check(arg_val)
        else:
            interpret_exit('operand_type', 'neocekavany typ argumentu na druhe pozici instrukce cislo ' + str(instr_order))
    elif arg_pos == 3:
        if ( instr_pos >= 20 and instr_pos <= 34 ):
            sym_regex_check(arg_val)
            sym_typecheck(instr_order, arg_val, arg_pos)
        else:
            interpret_exit('operand_type', 'neocekavany typ argumentu na treti pozici instrukce cislo ' + str(instr_order))
    else:
        interpret_exit('internal', 'arg_check_type_value: spatna pozice argumentu (mimo seznam)')

## vrati kolik argumentu ma mit zadana instrukce podle pozice v serazenem poli ##
def arg_check_type_switch(index):
    if index < 5:                       # instrukce s zadnym argumentem
        return 0
    elif index >= 5 and index <= 13:    # 1
        return 1
    elif index >= 14 and index <= 19:   # 2
        return 2
    elif index > 19:                    # 3
        return 3

### regexy pro kontrolu promennych, labelu, atd. ###
def var_regex_check(text):
    if text == None:
        text = ""
    if not (regex.match(r'^(LF|GF|TF)@[a-zA-Z#&!?%_*$][a-zA-Z#&!?%_*$0-9]*$' ,text)):
        interpret_exit('lexical', 'spatny format promenne')
        interpret_exit()
def label_regex_check(text):
    if text == None:
        text = ""
    if not (regex.match(r'^[a-zA-Z#&!?%_*\\$0-9]*$' ,text)):
        interpret_exit('lexical', 'spatny format navesti')

def sym_regex_check(text):
    if text == None:
        text = ""
    if not (regex.match(r'(LF|GF|TF)@[a-zA-Z#&!?%_*$][a-zA-Z#&!?%_*$0-9]*' ,text)) and not (regex.match(r'[a-zA-Z#&!?%_*\\$0-9]*', text)):
        interpret_exit('lexical', 'spatny format symbolu')

def type_regex_check(text):
    if text == None:
        text = ""
    if not (regex.match(r'(int|string|bool|nil)' ,text)):
        interpret_exit('lexical', 'spatny format typu')

## kontrola typu symbolu (konstanty) ##
def sym_typecheck(instr_order, arg_val, arg_pos):
    index = arg_find(instr_order)
    if index < 0:
        interpret_exit('internal', 'sym_typecheck: nenalezeny argumenty pro danou instrukci')
    arglist = PROG_ARGS[index]
    type = arg_get(arglist, arg_pos+3)
    sym_type_regex_check(arg_val, type, instr_order)

## lexikalni kontrola hodnoty symbolu (konstanty) ##
def sym_type_regex_check(text, type, instr_order):
    if text == None:
        text = ""
    if type == 'int':
        if not (regex.match(r'^[0-9\-]+$', text)):
            interpret_exit('lexical', 'uvedeny typ \'' + type + '\' obsahuje nepovolene znaky ci nepovolenou hodnotu')
    elif type == 'string':
        if not (regex.match(r'[a-zA-Z#&*$0-9]*', text)):
            interpret_exit('lexical', 'uvedeny typ \'' + type + '\' obsahuje nepovolene znaky ci nepovolenou hodnotu')
    elif type == 'bool':
        if not (regex.match(r'(true|false)', text)):
            interpret_exit('lexical', 'uvedeny typ \'' + type + '\' obsahuje nepovolene znaky ci nepovolenou hodnotu')
    elif type == 'nil':
        if not (regex.match(r'[nil]', text)):
            interpret_exit('lexical', 'uvedeny typ \'' + type + '\' obsahuje nepovolene znaky ci nepovolenou hodnotu')
    elif type == 'var':
        if not (regex.match(r'^(LF|GF|TF)@[a-zA-Z#&!?%_*$][a-zA-Z#&!?%_*$0-9]*$', text)):
            interpret_exit('lexical', 'uvedeny typ \'' + type + '\' obsahuje nepovolene znaky ci nepovolenou hodnotu')
    else:
        interpret_exit('operand_type', 'neplatny typ konstanty \'' + type + '\' v argumentu pri ' + str(instr_order) + '. instrukci')

## prida promennou do seznamu (pokud byla nekde definovana) ##
def var_add(name, order):
    global PROG_VARS
    insertion_data = [name, order]
    if instr_getname(order) == 'DEFVAR':
        PROG_VARS.append(insertion_data)

## najde v seznamu promennou a vrati dvojci (name, order) nebo None ##
def var_get(name):
    for variable in PROG_VARS:
        if variable[0] == name:
            return variable
    return None

## najde v seznamu promennou a vrati index v poli PROG_VARS nebo -1 ##
def var_get_index(name):
    i = 0
    for variable in PROG_VARS:
        if variable[0] == name:
            return i
        i = i + 1
    return -1

## vrati value / type podle element ##
def var_get_order(name):
    variable = var_get(name)
    if variable == None:
        interpret_exit('internal', 'var_get_data: promenna ' + name + ' nenalezena')
    return variable[1]

## odstrani promennou ze seznamu ##
def var_remove(name):
    index = var_get_index(name)
    if index < 0:
        interpret_exit('internal', 'var_remove: promenna ' + name + ' nenalezena')
    PROG_VARS.remove(PROG_VARS[index])

## prida navesti do seznamu ##
def label_add(name, order):
    global PROG_LABELS
    data = [name, order]
    if not (label_exists(name)):
        PROG_LABELS.append(data)
    else:
        interpret_exit(52, 'ruzna navesti se stejnym jmenem (\''+name+'\')')

## vrati true pokud navesti existuje, false pokud ne ##
def label_exists(name):
    for label in PROG_LABELS:
        if label[0] == name:
            return True
    return False

## vrati jmeno navesti nebo None ##
def label_get(name):
    for label in PROG_LABELS:
        if label[0] == name:
            return label[1]
        
    interpret_exit(52, 'navesti neexistuje')

## odstrani navesti ze seznamu ##
def label_remove(name):
    global PROG_LABELS
    i = 0
    index = -1
    data = []
    for label in PROG_LABELS:
        if label[0] == name:
            index = i
            data = [label[0], label[1]]
        i = i + 1
    if index < 0:
        interpret_exit('internal', 'label_remove: navesti ' + name + ' nenalezeno')
    PROG_LABELS.remove(data)

## prida volani do seznamu ##
def call_add(label_name, order, status='loaded'):
    global PROG_CALLS
    data = [label_name, order, status]
    PROG_CALLS.append(data)

## nastavi hodnotu status na value ('loaded', 'called', 'returned') ##
def call_set(order, value):
    if value != 'loaded' and value != 'called' and value != 'returned':
        interpret_exit('internal', 'call_set: spatna hodnota statusu pro volani na poradi ' + str(order))
    found = False
    for call in PROG_CALLS:
        if call[1] == order:
            call[2] = value
            found = True
    if found == False:        
        interpret_exit('internal', 'call_set: volani na poradi ' + str(order) + ' neexistuje')

## odstrani volani ze seznamu ##
def call_remove(order):
    global PROG_CALLS
    i = 0
    index = -1
    data = []
    for call in PROG_CALLS:
        if call[1] == order:
            index = i
            data = [call[0], call[1], call[2]]
        i = i + 1
    if index < 0:
        interpret_exit('internal', 'call_remove: volani ' + str(order) + ' nenalezeno')
    PROG_CALLS.remove(data)


## prida volani do seznamu ##
def callstack_push(order):
    global PROG_CALLSTACK
    data = order
    PROG_CALLSTACK.append(data)
    if len(PROG_CALLSTACK) > REC_LIMIT and RECURSIVE_STOP == True:
        interpret_exit(101, 'interpret ukoncen, protoze byl presahnut limit '+str(REC_LIMIT)+' volanych funkci.')
    if len(PROG_CALLSTACK) == 10000:
        verbose_print('[!!!] Zasobnik volani obsahuje pres 10 000 volanych funkci')

## odstrani volani ze seznamu ##
def callstack_pop():
    global PROG_CALLSTACK
    if len(PROG_CALLSTACK) != 0:
        return PROG_CALLSTACK.pop()
    else:
        interpret_exit('missing_value', 'zasobnik volani je prazdny')

## prida ramec do seznamu-zasobniku ##
def frame_push():
    global PROG_FRAMES
    data = []
    PROG_FRAMES.append(data)

## prida do ramce promennou (pokud neni upresnen ramec, defaultni hodnota je GF) ##
def frame_varadd(var_name, instr_order, frametype={'GF', 'LF', 'TF', 0, 1, -1}, var_value=None):
    global PROG_FRAMES
    if frametype != 'GF' and frametype != 'LF' and frametype != 'TF' and frametype != 0 and frametype != 1 and frametype != -1:
        frametype = 'GF'
    var = [var_name, var_value, instr_order, None]
    if frame_vardefined(var_name, frametype) == True:
        interpret_exit(52, 'redefinice promenne')

    if frametype == 'GF' or frametype == 0:
        PROG_FRAMES[0].append(var)
    elif frametype == 'LF' or frametype == -1:
        if len(PROG_FRAMES) == 2:
            interpret_exit(55, 'prace s neexistujicim ramcem')
        PROG_FRAMES[-1].append(var)
    elif frametype == 'TF' or frametype == 1:
        if frame_tf_get() == True:
            PROG_FRAMES[1].append(var)
        else:
            interpret_exit('no_frame', 'promenna '+var_name+' pracuje s docasnym ramcem (TF@), ktery neexistuje')

## zjisti zda je promenna v ramci definovana, vraci True nebo False ##
def frame_vardefined(var_name, frametype={'GF', 'LF', 'TF', 0, 1, -1}):
    if frametype == 'GF' or frametype == 0:
        index = 0
    elif frametype == 'LF' or frametype == -1:
        index = -1
    elif frametype == 'TF' or frametype == 1:
        if frame_tf_get() == True:
            index = 1
        else:
            return False
    
    for variable in PROG_FRAMES[index]:
        if variable[0] == var_name:
            return True
    return False

## nastavi hodnotu promenne v ramci, vrati True nebo False podle uspechu operace ##
def frame_varset(var_name, var_value, frametype={'GF', 'LF', 'TF', 0, 1, -1}, instr_order=None):
    global PROG_FRAMES
    if frametype == 'GF' or frametype == 0:
        index = 0
    elif frametype == 'LF' or frametype == -1:
        index = -1
    elif frametype == 'TF' or frametype == 1:
        if frame_tf_get() == True:
            index = 1
        else:
            return False    
    try:
        int(var_value)
        exp_type = 'int'
    except:
        if var_value == 'true' or var_value == 'false':
            exp_type = 'bool'
            if instr_order != None:
                ind = arg_find(instr_order)
                if ind < 0:
                    interpret_exit('internal', 'frame_varset: nenalezeny argumenty k instrukci')
                i=0
                for argument in PROG_ARGS[ind]:
                    if argument == var_value:
                        exp_type = PROG_ARGS[ind][i+3]
                    i=i+1
                if exp_type == 'var':
                    exp_type = 'bool'
        elif var_value == 'nil':
            exp_type = 'nil'
        else:
            exp_type = 'string'
            if var_value == None:
                var_value = ''
    
    for variable in PROG_FRAMES[index]:
        if variable[0] == var_name:
            variable[1] = var_value
            variable[3] = exp_type
            #elif variable[3] != exp_type:      
            #    interpret_exit('semantic', 'nekompatibilni typy - hodnota: '+exp_type+', promenna: '+variable[3])

    return False

## vraci hodnotu promenne nebo False pokud je uveden spatny ramec, True pokud promenna existuje ale nema hodnotu, None pokud promenna neexistuje ##
def frame_varget(var_name, frametype={'GF', 'LF', 'TF', 0, 1, -1}):
    global PROG_FRAMES
    if frametype == 'GF' or frametype == 0:
        index = 0
    elif frametype == 'LF' or frametype == -1:
        index = -1
    elif frametype == 'TF' or frametype == 1:
        if frame_tf_get() == True:
            index = 1
        else:
            return False
    
    for variable in PROG_FRAMES[index]:
        if variable[0] == var_name:
            if variable[1] == None:
                return True
            else:
                return variable[1]
    return None

## vraci typ promenne nebo none pri spatnem ramci ci false pokud promenna neexistuje ##
def frame_varget_type(var_name, frametype={'GF', 'LF', 'TF', 0, 1, -1}):
    global PROG_FRAMES
    if frametype == 'GF' or frametype == 0:
        index = 0
    elif frametype == 'LF' or frametype == -1:
        index = -1
    elif frametype == 'TF' or frametype == 1:
        if frame_tf_get() == True:
            index = 1
        else:
            return None
    for variable in PROG_FRAMES[index]:
        if variable[0] == var_name:
            return variable[3]
    return False   

## nastavi typ promenne ##
def frame_varset_type(var_name, var_value, frametype={'GF', 'LF', 'TF', 0, 1, -1}):
    global PROG_FRAMES
    if frametype == 'GF' or frametype == 0:
        index = 0
    elif frametype == 'LF' or frametype == -1:
        index = -1
    elif frametype == 'TF' or frametype == 1:
        if frame_tf_get() == True:
            index = 1
        else:
            return None
    
    for variable in PROG_FRAMES[index]:
        if variable[0] == var_name:
            variable[3] = var_value
    return False    

## inicializuje zasobnik ramcu, 0 ... GF, 1 ... TF ##
def frame_init():
    global PROG_FRAMES
    frame_push()
    frame_push()

## smaze cely zasobnik ramcu (vcetne GF a TF) ##
def frame_destruct():
    global PROG_FRAMES
    while len(PROG_FRAMES) != 0:
        PROG_FRAMES.pop()

def frame_tf_set(bool):
    global TEMP_FR
    TEMP_FR = bool

def frame_tf_get():
    return TEMP_FR

## odebere ramec ze seznamu-zasobniku ##
def frame_pop():
    global PROG_FRAMES
    if len(PROG_FRAMES) > 2:
        PROG_FRAMES.pop()
    else:
        interpret_exit(55, 'proveden POPFRAME nad prazdnym zasobnikem ramcu')

## zjisti do jakeho ramce promenna patri, vrati:    0 -> GF     1 -> TF     -1 -> LF ##
def var_get_frame(var_name):
    if var_name == None:
        return 2
    edit = var_name.split('@')
    if edit[0] == 'GF':
        return 0
    elif edit[0] == 'TF':
        return 1
    elif edit[0] == 'LF':
        return -1
    else:
        return 2

## pushne hodnotu na zasobnik ##
def progstack_push(value, type):
    global PROG_STACK
    data = [value, type]
    PROG_STACK.append(data)

## odstrani a vrati posledni vlozenou hodnotu ze zasobniku ##
def progstack_pop():
    global PROG_STACK
    if len(PROG_STACK) != 0:
        return PROG_STACK.pop()
    else:
        interpret_exit('missing_value', 'zasobnik je prazdny')

def checkType(instr_name, instr_type, type, var_name, type2=None):
    if instr_type != type and instr_type != type2:
        if instr_type == None:
            frame_varset_type(var_name, type, var_get_frame(var_name))
            return
        elif instr_type == 'var':
            value = frame_varget_type(var_name, var_get_frame(var_name))
            if value != type:
                if value == None:
                    frame_varset_type(var_name, type, var_get_frame(var_name))
                    return
                if value != type2:
                    interpret_exit('operand_type', 'spatny typ operandu instrukce '+instr_name)
            return
        else:
            interpret_exit('operand_type', 'spatny typ operandu instrukce '+instr_name)

def removeEscapes(string):
    index = -1
    i = 0
    watchOut = False
    code = ""
    replacement = ""
    for c in string:
        if watchOut == True:
            if len(code) == 3:
                watchOut = False
            else:
                code = code + c
        if c == '\\' and index < 0:
            index = i
            watchOut = True
        i = i + 1

    if index < 0 or len(code) < 3:
        return string
    try:
        int(code)
    except:
        return string
    if int(code) > 0 and int(code) < 128:
        replacement = chr(int(code))
    else:
        interpret_exit('string_error', 'neznamy escape kod')
    newstring = string[:index] + replacement + string[index + 4:]
    newstring = removeEscapes(newstring)
    return newstring
    
    


###
### PARSING ARGUMENTU

## parsovani argumentu skriptu pomoci argparse ##
def parseScriptArguments():
    interpret = argparse.ArgumentParser(description='Interpret IPPcode21, interpretuje kod. Alespon jeden z parametru (--source nebo --input) musi byt vzdy zadan. Pokud jeden z nich chybi, jsou chybejici data nacitana ze standardniho vstupu.')
    interpret.add_argument('--verbose', '-v', required=False, action='store_true',
                    help='skript bude hlasit podrobny postup analyzy a interpretace')
    interpret.add_argument('--recursive', '-rs', required=False, action='store_true',
                    help='interpretace kodu: v pripade velkeho zanoreni pri volani funkci se skript ukonci')
    interpret.add_argument('--deparse', '-d', required=False, action='store_true',
                    help='neinpretovat kod, pouze vypsat zdrojovy kod v IPPcode21')
    semi_required = interpret.add_argument_group('argumenty skriptu')
    semi_required.add_argument('--source', required=False, metavar='file', type=str,
                    help='vstupni soubor s XML reprezentaci zdrojoveho kodu')
    semi_required.add_argument('--input', required=False, metavar='file', type=str,
                    help='soubor se vstupy pro samotnou interpretaci zadaneho zdrojoveho kodu')
    
    try:
        script_args = interpret.parse_args()
    except SystemExit as c:
        if int(str(c)) != 0:
            c = 10
        else:
            c = 0
        exit(int(c))

    return script_args

## parsovani argumentu '--source' a '--input' vcetne otevreni souboru pro cteni ##
def checkScriptArguments():
    global SOURCE
    global INPUT
    global INPUT_F
    global SOURCE_F

    if not SOURCE and not INPUT:
        interpret_exit('args', 'alespon jeden z argumentu \'--source\' nebo \'--input\' musi byt uveden')
    elif SOURCE and not INPUT:
        try:
            SOURCE_F = open(SOURCE, "r")
        except FileNotFoundError:
            interpret_exit('input', 'zdrojovy soubor nebyl nalezen')
        except:
            interpret_exit('input', 'neocekavana vyjimka pri otevreni zdrojoveho souboru')
    elif not SOURCE and INPUT:
        try:
            INPUT_F = open(INPUT, "r")
        except FileNotFoundError:
            interpret_exit('input', 'soubor se vstupem k interpretaci nebyl nalezen')
        except:
            interpret_exit('input', 'neocekavana vyjimka pri otevreni souboru se vstupem k interpretaci')
    elif SOURCE and INPUT:
        try:
            SOURCE_F = open(SOURCE, "r")
        except FileNotFoundError:
            interpret_exit('input', 'zdrojovy soubor nebyl nalezen')
        except:
            interpret_exit('input', 'neocekavana vyjimka pri otevreni zdrojoveho souboru')
        try:
            INPUT_F = open(INPUT, "r")
        except FileNotFoundError:
            interpret_exit('input', 'soubor se vstupem k interpretaci nebyl nalezen')
        except:
            interpret_exit('input', 'neocekavana vyjimka pri otevreni souboru se vstupem k interpretaci')

    if SOURCE == INPUT:
        verbose_print('Varovani: zdrojovy soubor (--source) je stejny jako soubor se vstupem k interpretaci (--input)')   


###
### PARSING XML

## zkontroluje spravny XML format (well-formed), spravny format dle zadani (hlavicku, instrukce, jejich poradi, argumenty) tj. tagy, atributy (nekontroluje hodnoty tagu), vcetne kontroly platnosti instrukci ##
def sourceXMLparse():
    verbose_print('------ [KONTROLA ZDROJOVEHO SOUBORU] ------')

    try:
        if (SOURCE_F != 0):
            source_tree = xml_et.parse(SOURCE_F)
        else:
            source_tree = xml_et.fromstring(SOURCE_F_IN)
    except xml_et.ParseError:
        interpret_exit('XMLformat', 'zdrojovy soubor nema spravny format XML')
    except:
        interpret_exit('XMLformat', 'neocekavana nebo neosetrena vyjimka pri parsovani zdrojoveho souboru XML')
    verbose_print('Kontrola XML formatu OK')

    if (SOURCE_F != 0):
        root = source_tree.getroot()
    else:
        root = source_tree
    sourceXMLparse_header(root)

    instr_cnt = 1
    instr_name = "UNDEFINED_INSTRUCTION"
    for child in root:
        sourceXMLparse_instr(child, instr_cnt)
        sourceXMLparse_arg(child)
        instr_cnt = instr_cnt + 1
    
    instr_list_valid()

## kontrola hlavicky ##
def sourceXMLparse_header(root):
    if root.tag != 'program':
        interpret_exit('XMLstruct', 'spatny format hlavicky zdrojoveho souboru (chybi tag \'<program>\')')
    
    head_attrib = list(root.attrib)
    if not ('language' in head_attrib):
        interpret_exit('XMLstruct', 'spatny format hlavicky zdrojoveho souboru (neuveden atribut \'languae\')')
    head_keys = list(root.attrib.values())
    if not ('IPPcode21' in head_keys):
        interpret_exit('XMLstruct', 'spatny format hlavicky zdrojoveho souboru (neplatna hodnota atributu \'language\' - vstup: ' + head_keys[0] + ', ocekavano: IPPcode21)')
    for attribute in head_attrib:
        if (attribute != 'language') and (attribute != 'name') and (attribute != 'description'):
            interpret_exit('XMLstruct', 'spatny format hlavicky zdrojoveho souboru (uveden neplatny atribut)')

    verbose_print('Hlavicka OK')

## kontrola instrukce ##
def sourceXMLparse_instr(child, instr_cnt):
    if child.tag != "instruction":
            interpret_exit('XMLstruct', 'spatny format zdrojoveho souboru (obsah neni tvoren pouze instrukcemi, \'<instruction>\')')
    ca = list(child.attrib.keys())
    if not ('order' in ca) or not ('opcode' in ca):
        interpret_exit('XMLstruct', 'spatny format zdrojoveho souboru (tag \'<instruction>\' neobsahuje atribut \'order\' nebo \'opcode\')')

    vals = list(child.attrib.values())
    try:
        order_vals = int(vals[0])
    except:
        interpret_exit('XMLstruct', 'spatny format zdrojoveho souboru (poradi instrukce neni cislo)')
    if order_vals <= 0:
        interpret_exit('XMLstruct', 'spatny format zdrojoveho souboru (zaporne ci nulove poradi instrukce)')

    instr_name = vals[1].upper()
    if not (instr_name in INSTR_LIST):
        interpret_exit('XMLstruct', 'neznama instrukce \'' + instr_name + '\'')

    instr_add(instr_name, vals[0])
    verbose_print('[CHK:'+ str(instr_cnt) + ']' + ' Instrukce \'' + instr_name + '\' OK')

## kontrola argumentu instrukce ##
def sourceXMLparse_arg(child):
    count = 0
    for subelem in child:
        if not (regex.match(r'arg[123]', subelem.tag)):
            interpret_exit('XMLstruct', 'spatny format zdrojoveho souboru (obsah tagu \'<instruction>\' je tvoren jinymi tagy nez \'<arg[123]>\')')

        arg_keys = list(subelem.attrib.keys())
        if len(arg_keys) != 1 or arg_keys[0] != 'type':
            interpret_exit('XMLstruct', 'spatny format zdrojoveho souboru (tag \'<arg[123]>\' neobsahuje pouze atribut \'type\')')
            
        arg_vals = list(subelem.attrib.values())
        if len(arg_vals) != 1 or (arg_vals[0] != 'var' and arg_vals[0] != 'label' and arg_vals[0] != 'type' and arg_vals[0] != 'int' and arg_vals[0] != 'string' and arg_vals[0] != 'bool' and arg_vals[0] != 'nil'):
            interpret_exit('XMLstruct', 'spatny format zdrojoveho souboru (atribut \'type\' tagu \'<arg[123]>\' obsahuje neplatnou hodnotu)')
        
        instr_order = int(list(child.attrib.values())[0])

        if arg_vals[0] == 'label':
            if instr_getname(instr_order) == 'LABEL':
                label_add(subelem.text, instr_order)
            elif instr_getname(instr_order) == 'CALL':
                call_add(subelem.text, instr_order)

        arg_number = subelem.tag.split('arg')[1]
        verbose_print('\t nalezen ' + arg_number + '. argument' )
        count = count + 1
        arg_set(instr_order , int(arg_number), subelem.text, arg_vals[0])
        
    instr_modify_argcnt(instr_find(int(list(child.attrib.values())[0])), count)

###
### INTERPRETACE

## interpretuje kod ##
def instruction_execute(instr_order):
    arg1, arg2, arg3, type_1, type_2, type_3, instr_name = instruction_execute_prepare(instr_order)
    verbose_print('[INT:'+str(instr_order)+'] ', end='')

    if (instr_name == 'CREATEFRAME'):
        frame_tf_set(True)
        verbose_print('Pouziva se docasny ramec')
    elif instr_name == 'PUSHFRAME':
        if frame_tf_get() != True:
            interpret_exit(55, 'pouzita instrukce PUSHFRAME pri prazdnem zasobniku')
        frame_tf_set(False)
        frame_push()
        while len(PROG_FRAMES[1]) != 0:
            var = PROG_FRAMES[1].pop()
            var[0] = 'LF@' + var[0].split('@')[1]
            PROG_FRAMES[-1].append(var)
        verbose_print('Vytvoren novy lokalni ramec')
    elif instr_name == 'POPFRAME':
        while len(PROG_FRAMES[-1]) != 0 and len(PROG_FRAMES) > 2:
            var = PROG_FRAMES[-1].pop()
            var[0] = 'TF@' + var[0].split('@')[1]
            PROG_FRAMES[1].append(var)
        frame_pop()
        frame_tf_set(True)
        verbose_print('Lokalni ramec odebran')
    elif instr_name == 'RETURN':
        last_call = callstack_pop()
        verbose_print('Probiha navrat z volani funkce na instrukci '+str(instr_order))
        return last_call + 1
    elif instr_name == 'BREAK':
        verbose_print('Breakpoint. STDERR: \'', end='')
        print('[BREAKPOINT] Instrukce: '+str(instr_order)+', Provedeno: '+str(INSTR_EXECED)+' instrukci, obsahy zasobniku:', file=sys.stderr)
        print('Ramce [G,T,L]: '+str(PROG_FRAMES), file=sys.stderr)
        print('Volani [order]: '+str(PROG_CALLSTACK), file=sys.stderr)
        verbose_print('\'')

    elif instr_name == 'DEFVAR':
        frame = var_get_frame(arg1)
        frame_varadd(arg1, instr_order, frame)
        verbose_print('Definovana nova promenna \''+arg1+'\'')
    elif instr_name == 'POPS':
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame != 2:
            if frame_varget(arg1, frame) == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
        value, type = progstack_pop()
        frame_varset(arg1, value, frame)
        frame_varset_type(arg1, type, frame)
        verbose_print('Vyjmuta posledni hodnota ze zasobniku '+value+' => '+arg1)
    elif instr_name == 'CALL':
        callstack_push(instr_order)
        verbose_print('Volani funkce \''+arg1+'\'')
        return label_get(arg1)
    elif instr_name == 'LABEL':
        verbose_print('Navesti \'' + arg1 + '\'')
    elif instr_name == 'JUMP':
        verbose_print('Skok na navesti \''+ arg1 + '\'')
        return label_get(arg1)
    elif instr_name == 'PUSHS':
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame != 2:
            if frame_varget(arg1, frame) == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if frame_varget(arg1, frame) == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        if frame == 2:
            try:
                int(arg1)
                type = 'int'
            except:
                if arg1 == 'false' or arg1 == 'true':
                    type = 'bool'
                elif arg1 == 'nil':
                    type = 'nil'
                else:
                    type = 'string'
            progstack_push(arg1, type)
        else:
            value = frame_varget(arg1, frame)
            progstack_push(value, frame_varget_type(arg1, frame))
        verbose_print('Pridano na vrchol zasobniku \''+arg1+'\'')
    elif instr_name == 'WRITE':
        verbose_print('STDOUT: \'', end='')
        if type_1 == 'nil':
            print("", end='')
        else:
            frame = var_get_frame(arg1)
            if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if frame != 2:
                if frame_varget(arg1, frame) == None:
                    interpret_exit(54, 'prace s nedefinovanou promennou')
                if frame_varget(arg1, frame) == True:
                    interpret_exit(56, 'prace s promennou bez hodnoty')
            if frame == 2:
                value = removeEscapes(str(arg1))
                print(value, end='')
            else:
                value = frame_varget(arg1, frame)
                if value != None:
                    if value == 'nil' and frame_varget_type(arg1, frame) == 'nil':
                        print('', end='')
                    else:
                        print(removeEscapes(str(value)), end='')
                else:
                    interpret_exit('no_frame', 'promenna v tomto ramci neexistuje')
        verbose_print('\'')
    elif instr_name == 'EXIT':
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame != 2:
            if frame_varget(arg1, frame) == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            value = frame_varget(arg1, frame)
            if value == True:
                interpret_exit(56, 'chybi hodnota v promenne')
            if frame_varget_type(arg1, frame) != 'int':
                interpret_exit(53, 'spatny typ operandu')
            arg1 = value
        else:
            checkType(instr_name, type_1, 'int', arg1)
        if int(arg1) < 0 or int(arg1) > 49:
            interpret_exit('bad_value', 'neplatny navratovy kod instrukce EXIT')
        verbose_print('Interpretace ukoncena instrukci EXIT s navratovym kodem ' + arg1)
        exit(int(arg1))
    elif instr_name == 'DPRINT':
        verbose_print('STDERR: \'', end='')
        if type_3 == 'nil':
            print("", end='', file=sys.stderr)
        else:
            print(arg1, end='', file=sys.stderr)
        verbose_print('\'')

    elif instr_name == 'MOVE':
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        f_2 = var_get_frame(arg2)
        if f_2 != 2:
            value = frame_varget(arg2, f_2)
            arg2 = value
            if (f_2 == 1 and frame_tf_get() == False) or (f_2 == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if arg2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if arg2 == True:
                interpret_exit(56, 'chybejici hodnota v promenne')
        frame_varset(arg1, arg2, frame, instr_order)
        verbose_print('Do promenne \''+arg1+'\' ulozena hodnota \''+str(arg2)+'\'')
    elif instr_name == 'INT2CHAR':
        a2_f = var_get_frame(arg2)
        if a2_f != 2:
            type_2 = frame_varget_type(arg2, a2_f)
            arg2 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() != True) or (len(PROG_FRAMES) == 2 and a2_f == -1):
                interpret_exit(55, 'prace s neexistujicim ramcem')
            if arg2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if arg2 == True:
                interpret_exit(56, 'chybi hodnota v promenne')
            if type_2 != 'int':
                interpret_exit(53, 'spatny typ operandu instrukce INT2CHAR')
        else:
            checkType(instr_name, type_2, 'int', arg2)
        try:
            char = chr(int(arg2))
        except:
            interpret_exit(58, 'nevalidni UNICODE hodnota znaku pro konverzi INT2CHAR')
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        frame_varset(arg1, char, frame)
        verbose_print('INT2CHAR: ' + arg2 + ' -> ' + char)
    elif instr_name == 'NOT':
        frame = var_get_frame(arg1)
        fr_2 = var_get_frame(arg2)
        if fr_2 != 2:
            value = frame_varget(arg2, fr_2)
            type_2 = frame_varget_type(arg2, fr_2)
            arg2 = value
            if (fr_2 == 1 and frame_tf_get() != True) or (len(PROG_FRAMES) == 2 and fr_2 == -1):
                interpret_exit(55, 'prace s neexistujicim ramcem')
            if arg2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if arg2 == True:
                interpret_exit('missing_value', 'chybi hodnota v promenne')
            if type_2 != 'bool':
                interpret_exit(53, 'spatny typ operandu instrukce NOT')
        else:
            checkType(instr_name, type_2, 'bool', arg2)
        
        if frame != 2:
            arg1_name = arg1
            value = frame_varget(arg1, frame)
            type_1 = frame_varget_type(arg1, frame)
            arg1 = value
            if (frame == 1 and frame_tf_get() != True) or (len(PROG_FRAMES) == 2 and frame == -1):
                interpret_exit(55, 'prace s neexistujicim ramcem')
            if arg1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')

        if arg2 == 'true':
            value = 'false'
        else:
            value = 'true'
        
        frame_varset(arg1_name, value, frame)
        verbose_print('NOT: '+str(arg1_name)+' => '+value)
    elif instr_name == 'STRLEN':
        fr_2 = var_get_frame(arg2)
        if fr_2 != 2:
            value = frame_varget(arg2, fr_2)
            type_2 = frame_varget_type(arg2, fr_2)
            arg2 = value
            if (fr_2 == 1 and frame_tf_get() != True) or (len(PROG_FRAMES) == 2 and fr_2 == -1):
                interpret_exit(55, 'prace s neexistujicim ramcem')
            if arg2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if arg2 == True:
                interpret_exit('missing_value', 'chybi hodnota v promenne')
            if type_2 != 'string':
                interpret_exit(53, 'spatny typ operandu instrukce STRLEN')
        else:
            checkType(instr_name, type_2, 'string', arg2)
        if arg2 == None:
            arg2 = ""
        leng = len(arg2)
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        frame_varset(arg1, leng, frame)
        verbose_print('STRLEN: ' + str(leng) + ' <= ' + arg1)
    elif instr_name == 'TYPE':
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        a2_f = var_get_frame(arg2)
        arg2_name = arg2
        if a2_f != 2:
            value = frame_varget(arg2, a2_f)
            type_2 = frame_varget_type(arg2, a2_f)
            arg2 = value
            if (a2_f == 1 and frame_tf_get() != True) or (len(PROG_FRAMES) == 2 and a2_f == -1):
                interpret_exit(55, 'prace s neexistujicim ramcem')
            if arg2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if arg2 == True:
                arg2 = ''
            
        if a2_f == 2:
            try:
                int(arg2)
                result = 'int'
            except:
                if arg2 == 'true' or arg2 == 'false':
                    result = 'bool'
                elif arg2 == 'nil':
                    result = 'nil'
                else:
                    result = 'string'
        else:
            if frame_varget_type(arg2_name, a2_f) == None:
                result = ''
            elif frame_varget_type(arg2_name, a2_f) == False:
                interpret_exit(54, 'prace s neexistujici promennou')
            else:
                result = frame_varget_type(arg2_name, a2_f)
                
        frame_varset(arg1, result, frame)
        frame_varset_type(arg1, 'string', frame)
        verbose_print('TYPE ('+arg2_name+') => \''+str(result)+'\'')
    elif instr_name == 'READ':
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')

        fr_2 = var_get_frame(arg2)
        if fr_2 != 2:
            if (fr_2 == 1 and frame_tf_get() == False) or (fr_2 == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if frame_varget(arg2, frame) == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            arg2_name = arg2
            arg2 = frame_varget(arg2, fr_2)
            type_2 = frame_varget_type(arg2_name, fr_2)
        else:
            type_2 = arg2

        verbose_print('STDIN: ['+type_2+'] \'', end='')
        if INPUT_F == 0:
            try:
                load = input()
            except:
                load = 'nil'
        else:
            load = INPUT_F.read()
        value = str(load)
        if load == 'nil':
            value = 'nil'
        else:
            if (arg2 == 'bool'):
                if value.upper().split('\n')[0] != 'TRUE':
                    value = 'false'
                else:
                    value = 'true'
            elif (arg2 == 'int'):
                try:
                    value = int(load)
                except:
                    value = 'nil'
            elif (arg2 == 'string'):
                value = load

        verbose_print('\'')
        frame_varset(arg1, value, frame)
    elif instr_name == 'ADD':
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        cmp_1 = arg2
        cmp_2 = arg3
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        else:
            checkType(instr_name, type_2, 'int', arg2)
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        else:
            checkType(instr_name, type_3, 'int', arg3)
        result = int(cmp_1) + int(cmp_2)
        frame_varset(arg1, str(result),frame)
        verbose_print('ADD: '+arg2+' + '+arg3+' => '+str(result))
    elif instr_name == 'SUB':
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        cmp_1 = arg2
        cmp_2 = arg3
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        else:
            checkType(instr_name, type_2, 'int', arg2)
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        else:
            checkType(instr_name, type_3, 'int', arg3)
        result = int(cmp_1) - int(cmp_2)
        frame_varset(arg1, str(result),frame)
        verbose_print('SUB: '+arg2+' - '+arg3+' => '+str(result))
    elif instr_name == 'MUL':
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        cmp_1 = arg2
        cmp_2 = arg3
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        else:
            checkType(instr_name, type_2, 'int', arg2)
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        else:
            checkType(instr_name, type_3, 'int', arg3)
        result = int(cmp_1) * int(cmp_2)
        frame_varset(arg1, str(result),frame)
        verbose_print('MUL: '+arg2+' * '+arg3+' => '+str(result))
    elif instr_name == 'IDIV':
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        cmp_1 = arg2
        cmp_2 = arg3
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        else:
            checkType(instr_name, type_2, 'int', arg2)
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        else:
            checkType(instr_name, type_3, 'int', arg3)

        if int(arg3) == 0:
            interpret_exit(57, 'deleni nulou')
        result = int(cmp_1) // int(cmp_2)
        frame_varset(arg1, str(result),frame)
        verbose_print('IDIV: '+arg2+' / '+arg3+' => '+str(result))
    elif instr_name == 'LT':
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            type_2 = frame_varget_type(arg2, a2_f)
            arg2 = cmp_1
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            type_3 = frame_varget_type(arg3, a3_f)
            arg3 = cmp_2

        if type_2 != type_3:
            interpret_exit('operand_type', 'druhy a treti operand intrukce '+instr_name+' maji ruzne datove typy')
        if type_2 == 'int':
            result = int(arg2) < int(arg3)
        elif type_2 == 'bool':
            if arg2 == 'false':
                cmp_1 = 0
            else:
                cmp_1 = 1
            if arg3 == 'false':
                cmp_2 = 0
            else:
                cmp_2 = 1
            result = cmp_1 < cmp_2
        elif type_2 == 'string':
            if arg2 == None:
                arg2 = ''
            if arg3 == None:
                arg3 = ''
            result = removeEscapes(arg2) < removeEscapes(arg3)
        else:
            interpret_exit(53, 'instrukci '+instr_name+' nelze porovnavat operand typu nil')
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        if result:
            result = 'true'
        else:
            result = 'false'
        frame_varset(arg1, result, frame)
        verbose_print('LT: '+arg2+' < '+arg3+' => '+str(result))
    elif instr_name == 'GT':
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            type_2 = frame_varget_type(arg2, a2_f)
            arg2 = cmp_1
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            type_3 = frame_varget_type(arg3, a3_f)
            arg3 = cmp_2

        if type_2 != type_3:
            interpret_exit('operand_type', 'druhy a treti operand intrukce '+instr_name+' maji ruzne datove typy')
        if type_2 == 'int':
            result = int(arg2) > int(arg3)
        elif type_2 == 'bool':
            if arg2 == 'false':
                cmp_1 = 0
            else:
                cmp_1 = 1
            if arg3 == 'false':
                cmp_2 = 0
            else:
                cmp_2 = 1
            result = cmp_1 > cmp_2
        elif type_2 == 'string':
            if arg2 == None:
                arg2 = ''
            if arg3 == None:
                arg3 = ''
            result = removeEscapes(arg2) > removeEscapes(arg3)
        else:
            interpret_exit(53, 'instrukci '+instr_name+' nelze porovnavat operand typu nil')
        if result:
            result = 'true'
        else:
            result = 'false'
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        frame_varset(arg1, result, frame)
        verbose_print('GT: '+arg2+' > '+arg3+' => '+str(result))
    elif instr_name == 'EQ':
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            type_2 = frame_varget_type(arg2, a2_f)
            arg2 = cmp_1
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            type_3 = frame_varget_type(arg3, a3_f)
            arg3 = cmp_2

        if type_2 != type_3 and type_2 != 'nil' and type_3 != 'nil':
            interpret_exit('operand_type', 'druhy a treti operand intrukce '+instr_name+' maji ruzne datove typy')
        if type_2 != type_3:
            arg2 = 0
            arg3 = 1
            type_2 = 'int'

        if type_2 == 'int':
            result = int(arg2) == int(arg3)
        elif type_2 == 'bool':
            if arg2 == 'false':
                cmp_1 = 0
            else:
                cmp_1 = 1
            if arg3 == 'false':
                cmp_2 = 0
            else:
                cmp_2 = 1
            result = cmp_1 == cmp_2
        elif type_2 == 'nil':
            result = True
        elif type_2 == 'string':
            if arg2 == None:
                arg2 = ""
            if arg3 == None:
                arg3 = ""
            result = removeEscapes(arg2) == removeEscapes(arg3)
        
        if result == True:
            result = 'true'
        else:
            result = 'false'
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        frame_varset(arg1, result, frame)
        verbose_print('EQ: '+str(arg2)+' == '+str(arg3)+' => '+str(result))
    elif instr_name == 'AND':
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            arg2 = cmp_1
        else:
            checkType(instr_name, type_2, 'bool', arg2)
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            arg3 = cmp_2
        else:
            checkType(instr_name, type_3, 'bool', arg3)

        if (arg2 == 'true'):
            cmp_1 = 1
        else:
            cmp_1 = 0
        if (arg3 == 'true'):
            cmp_2 = 1
        else:
            cmp_2 = 0
        result = cmp_1 and cmp_2
        if result:
            result = 'true'
        else:
            result = 'false'
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        frame_varset(arg1, result, frame)
        verbose_print('AND: '+arg2+' and '+arg3+' => '+str(result))
    elif instr_name == 'OR':
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            arg2 = cmp_1
        else:
            checkType(instr_name, type_2, 'bool', arg2)
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            arg3 = cmp_2
        else:
            checkType(instr_name, type_3, 'bool', arg3)

        if (arg2 == 'true'):
            cmp_1 = 1
        else:
            cmp_1 = 0
        if (arg3 == 'true'):
            cmp_2 = 1
        else:
            cmp_2 = 0
        result = cmp_1 or cmp_2
        if result:
            result = 'true'
        else:
            result = 'false'
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        frame_varset(arg1, result, frame)
        verbose_print('OR: '+arg2+' or '+arg3+' => '+str(result))
    elif instr_name == 'STRI2INT':
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            type_2 = frame_varget_type(arg2, a2_f)
            arg2 = cmp_1
            if type_2 != 'string':
                interpret_exit(53, 'spatny typ operandu instrukce STRI2INT')
        else:
            checkType(instr_name, type_2, 'string', arg2)
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            type_3 = frame_varget_type(arg3, a3_f)
            if type_3 != 'int':
                interpret_exit(53, 'spatny typ operandu instrukce STRI2INT')
            arg3 = cmp_2
        else:
            checkType(instr_name, type_3, 'int', arg3)

        if int(arg3) >= len(arg2) or int(arg3) < 0:
            interpret_exit(58, 'indexace mimo meze retezce')
        result = ord(arg2[int(arg3)])
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        frame_varset(arg1, str(result), frame) 
        verbose_print('STRI2INT: '+str(result))
    elif instr_name == 'CONCAT':
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        else:
            checkType(instr_name, type_2, 'string', arg2)
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        else:
            checkType(instr_name, type_3, 'string', arg3)
        if arg2 == None:
            arg2 = ""
        if arg3 == None:
            arg3 = ""
        result = arg2 + arg3
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        frame_varset(arg1, str(result), frame)
        verbose_print('CONCAT: ' + str(result))
    elif instr_name == 'GETCHAR':
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        else:
            checkType(instr_name, type_2, 'string', arg2)
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
        else:
            checkType(instr_name, type_3, 'int', arg3)

        if int(arg3) >= len(arg2) or int(arg3) < 0:
            interpret_exit(58, 'indexace mimo meze retezce')
        result = arg2[int(arg3)]
        frame = var_get_frame(arg1)
        if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
            interpret_exit(55, 'prace s promennou v neexistujicim ramci')
        if frame_varget(arg1, frame) == None:
            interpret_exit(54, 'prace s nedefinovanou promennou')
        frame_varset(arg1, str(result), frame)
        verbose_print('GETCHAR: '+str(result))
    elif instr_name == 'SETCHAR':
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        frame = var_get_frame(arg1)
        if frame != 2:
            arg1_name = arg1
            cmp_1 = frame_varget(arg1, frame)
            type_1 = frame_varget_type(arg1, frame)
            if (frame == 1 and frame_tf_get() == False) or (frame == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if frame_varget(arg1, frame) == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            if type_1 != 'string':
                interpret_exit(53, 'spatny typ operandu SETCHAR')
            arg1 = cmp_1
        else:
            checkType(instr_name, type_1, 'string', arg1)
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            type_2 = frame_varget_type(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            if type_2 != 'int':
                interpret_exit(53, 'spatny typ operandu SETCHAR')
            arg2 = cmp_1
        else:
            checkType(instr_name, type_2, 'int', arg2)
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            type_3 = frame_varget_type(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            if type_3 != 'string':
                interpret_exit(53, 'spatny typ operandu SETCHAR')
            arg3 = cmp_2
        else:
            checkType(instr_name, type_3, 'string', arg3)

        if int(arg2) >= len(arg1) or int(arg2) < 0:
            interpret_exit(58, 'indexace mimo meze retezce')
        result = arg1
        if arg3 != None:
            arg3 = removeEscapes(arg3)
            result = result[:int(arg2)] + arg3[0] + result[int(arg2)+1:]
        else:
            interpret_exit(58, 'treti operand SETCHAR nesmi byt prazdny retezec')
        frame_varset(arg1_name, str(result), frame)
        verbose_print('SETCHAR: '+str(result))
    elif instr_name == 'JUMPIFEQ':
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            type_2 = frame_varget_type(arg2, a2_f)
            arg2 = cmp_1
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            type_3 = frame_varget_type(arg3, a3_f)
            arg3 = cmp_2

        if type_2 != type_3 and type_2 != 'nil' and type_3 != 'nil':
            interpret_exit('operand_type', 'druhy a treti operand intrukce '+instr_name+' maji ruzne datove typy')
        if type_2 != type_3:
            arg2 = 0
            arg3 = 1
            type_2 = 'int'

        if type_2 == 'int':
            result = int(arg2) == int(arg3)
        elif type_2 == 'bool':
            if arg2 == 'false':
                cmp_1 = 0
            else:
                cmp_1 = 1
            if arg3 == 'false':
                cmp_2 = 0
            else:
                cmp_2 = 1
            result = cmp_1 == cmp_2
        elif type_2 == 'nil':
            result = True
        elif type_2 == 'string':
            if arg2 == None:
                arg2 = ""
            if arg3 == None:
                arg3 = ""
            result = removeEscapes(arg2) == removeEscapes(arg3)
        
        if result == True:
            result = 'true'
        else:
            result = 'false'

        if not label_exists(arg1):
                interpret_exit(52, 'pozadovan skok na navesti, ktere neexistuje')
        if result == 'true':
            verbose_print('Proveden skok na navesti \''+arg1+'\'')
            return label_get(arg1)
        verbose_print('Skok nebyl proveden')
    elif instr_name == 'JUMPIFNEQ':
        a2_f = var_get_frame(arg2)
        a3_f = var_get_frame(arg3)
        if a2_f != 2:
            cmp_1 = frame_varget(arg2, a2_f)
            if (a2_f == 1 and frame_tf_get() == False) or (a2_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_1 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_1 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            type_2 = frame_varget_type(arg2, a2_f)
            arg2 = cmp_1
        if a3_f != 2:
            cmp_2 = frame_varget(arg3, a3_f)
            if (a3_f == 1 and frame_tf_get() == False) or (a3_f == -1 and len(PROG_FRAMES) == 2):
                interpret_exit(55, 'prace s promennou v neexistujicim ramci')
            if cmp_2 == None:
                interpret_exit(54, 'prace s nedefinovanou promennou')
            if cmp_2 == True:
                interpret_exit(56, 'prace s promennou bez hodnoty')
            type_3 = frame_varget_type(arg3, a3_f)
            arg3 = cmp_2

        if type_2 != type_3 and type_2 != 'nil' and type_3 != 'nil':
            interpret_exit('operand_type', 'druhy a treti operand intrukce '+instr_name+' maji ruzne datove typy')
        if type_2 != type_3:
            arg2 = 0
            arg3 = 1
            type_2 = 'int'

        if type_2 == 'int':
            result = int(arg2) == int(arg3)
        elif type_2 == 'bool':
            if arg2 == 'false':
                cmp_1 = 0
            else:
                cmp_1 = 1
            if arg3 == 'false':
                cmp_2 = 0
            else:
                cmp_2 = 1
            result = cmp_1 == cmp_2
        elif type_2 == 'nil':
            result = True
        elif type_2 == 'string':
            if arg2 == None:
                arg2 = ""
            if arg3 == None:
                arg3 = ""
            result = removeEscapes(arg2) == removeEscapes(arg3)
        
        if result == True:
            result = 'true'
        else:
            result = 'false'
        if not label_exists(arg1):
                interpret_exit(52, 'pozadovan skok na navesti, ktere neexistuje')
        if result == 'false':
            verbose_print('Proveden skok na navesti \''+arg1+'\'')
            return label_get(arg1)
        verbose_print('Skok nebyl proveden')
    else:
        interpret_exit('internal', 'instruction_execute: neznama instrukce')
    return instr_order + 1

## vraci arg1, arg2, arg3, typ_arg1, typ_arg2, typ_arg3, jmeno_instrukce ##
def instruction_execute_prepare(instr_order):
    instr_arg_i = arg_find(instr_order)
    if instr_arg_i < 0:
        interpret_exit('internal', 'instruction_execute: nenalazeny argumenty k instrukci')
    instr_args = PROG_ARGS[instr_arg_i]
    return arg_get(instr_args, 1), arg_get(instr_args, 2), arg_get(instr_args, 3), arg_get(instr_args, 4), arg_get(instr_args, 5), arg_get(instr_args, 6), instr_getname(instr_order)


###
### "MAIN"
###

# init

import gettext
gettext.gettext = convertArgparseMessages
import argparse
import sys
import xml.etree.ElementTree as xml_et
import re as regex

SOURCE = ""             # cesta ke zdrojovemu souboru
SOURCE_F = 0            # zdrojovy soubor
SOURCE_F_IN = ""        # promenna, kde bude ulozen kod v pripade ze bude zdroj predavan pres stdin
INPUT = ""              # cesta ke vstupu (ktery bude interpretovan)
INPUT_F = 0             # vstupni soubor
VERBOSE = False         # bude skript vice upovidany ?
TEMP_FR = False         # pracovat s TF ?
RECURSIVE_STOP = False  # pri velkem poctu volani funkci (rekurzi) nasilne ukoncit program
DEPARSE = False         # deparsovat ?
REC_LIMIT = 5000        # limit maximalniho poctu zanoreni pri volani funkci
PROG_INSTR = []         # seznam instrukci programu         # (jmeno_instrukce, order, nacteno_argumentu)
PROG_ARGS = []          # seznam argumentu programu         # (order, arg1, arg2, arg3, typ_arg1, typ_arg2, typ_arg3)

PROG_VARS = []          # seznam definovanych promennych v celem programu       # (jmeno_promenne, order)
PROG_LABELS = []        # seznam labelu-navesti             # (label, order)                        
PROG_CALLS = []         # seznam-zasobnik callu             # (call_instr_order, label, returned)           # returned=loaded,called,returned
PROG_FRAMES = []        # seznam-zasobnik ramcu             # [(var_name, var_value, var_order, var_type), ...]       # obsahuje seznamy, seznam=ramec, ktere obsahuji trojice-promenne   # [0] = GF ; [1] = TF ; rest = LF
PROG_CALLSTACK = []     # seznam-zasobnik volanych funkci   # (order)       # obsahuje ordery instrukci CALL
PROG_STACK = []         # seznam-zasobnik interpretovaneho programu # (value)   # obsahuje hodnoty


# seznam (povolenych) instrukci IPPcode21, serazene podle poctu parametru (0 - 3)
INSTR_LIST = ['CREATEFRAME', 'PUSHFRAME', 'POPFRAME', 'RETURN', 'BREAK',                                                                # 0-4
    'DEFVAR', 'POPS', 'CALL', 'LABEL', 'JUMP', 'PUSHS', 'WRITE', 'EXIT', 'DPRINT',                                                      # 5-13      # 5-6: var      # 7-9: label        # 10-13: sym
    'MOVE', 'INT2CHAR', 'NOT',  'STRLEN', 'TYPE', 'READ',                                                                               # 14-19     # 14-18: var, sym                   # 19: var, type
    'ADD', 'SUB', 'MUL', 'IDIV', 'LT', 'GT', 'EQ', 'AND', 'OR', 'STRI2INT', 'CONCAT', 'GETCHAR', 'SETCHAR', 'JUMPIFEQ', 'JUMPIFNEQ']    # 20-34     # 20-32: var, sym, sym              # 33-34: label, sym, sym

# kontrola argumentu skriptu

args = parseScriptArguments()
DEPARSE = args.deparse
SOURCE = args.source
INPUT = args.input
VERBOSE = args.verbose
RECURSIVE_STOP = args.recursive
checkScriptArguments()

# pro pripad ze zdrojovy soubor pochazi ze stdin

if SOURCE_F == 0:
    while True:
        try:
            line = input()
        except:
            break
        SOURCE_F_IN = SOURCE_F_IN + line + '\n'

# parsovani XML

sourceXMLparse()

# kontrola argumentu instrukci

verbose_print('------ [SYNTAKTICKE A SEMANTICKE KONTROLY] ------')
for instruction in PROG_INSTR:
    arg_check(instruction[1], instruction[2])
verbose_print('Kontroly argumentu v instrukcich OK')

# v pripade ze jen chceme zdrojovy kod ..

if DEPARSE:
    i = 0
    print(".IPPcode21\n")
    for instr in PROG_INSTR:
        arg1 = ""
        arg2 = ""
        arg3 = ""
        if PROG_ARGS[i][1+3] == "var" or PROG_ARGS[i][1+3] == "type":
            arg1 = PROG_ARGS[i][1]
        elif PROG_ARGS[i][1] != "":
            arg1 = PROG_ARGS[i][1+3] + "@" + PROG_ARGS[i][1]
        if PROG_ARGS[i][2+3] == "var" or PROG_ARGS[i][2+3] == "type":
            arg2 = PROG_ARGS[i][2]
        elif PROG_ARGS[i][2] != "":
            arg2 = PROG_ARGS[i][2+3] + "@" + PROG_ARGS[i][2]
        if PROG_ARGS[i][3+3] == "var" or PROG_ARGS[i][3+3] == "type":
            arg3 = PROG_ARGS[i][3]
        elif PROG_ARGS[i][3] != "":
            arg3 = PROG_ARGS[i][3+3] + "@" + PROG_ARGS[i][3]
        print(instr[0], arg1, arg2, arg3)
        i = i + 1
    exit(0)
verbose_print('------ [INTERPRETACE ZDROJOVEHO KODU] ------')
#################
#################

for label in PROG_LABELS:
    l_name = label[0]
    match = 0
    for label_2 in PROG_LABELS:
        l2_name = label[0]
        match = 0
        if (l_name == l2_name):
            match = match + 1
    if (match != 1):
        interpret_exit('semantic', 'navesti definovano vicekrat nez jednou (\''+l_name+'\' definovano '+str(match)+'x)')
verbose_print('Kontroly definic navesti OK')

for label in PROG_CALLS:
    if not label_exists(label[0]):
        interpret_exit('semantic', 'volani (poradi instrukce ' + str(label[1]) + ') odkazuje na navesti, ktere neexistuje')
verbose_print('Kontroly volani OK')

frame_init()
i = 1
INSTR_EXECED = 0
while True:
    if (len(PROG_INSTR) == 0 or i > PROG_INSTR[-1][1]):
        verbose_print('[INT:X] Konec interpretace')
        if len(PROG_FRAMES) != 2:
            verbose_print('Varoveni: interpretace ukoncena s neuvolnenymi ramci v zasobniku (neuvolneno: '+str(len(PROG_FRAMES)-2)+')')
        frame_destruct()
        if len(PROG_CALLSTACK) != 0:
            verbose_print('Varovani: interpretace ukoncena s neprazdnym zasobnikem volani (neuvolneno: '+str(len(PROG_CALLSTACK))+')')
        if len(PROG_STACK) != 0:
            verbose_print('Varovani: interpretace ukoncena s neprazdnym zasobnikem (neuvolneno: '+str(len(PROG_STACK))+')')
        exit(0)
    else:
        i = instruction_execute(i)
        INSTR_EXECED = INSTR_EXECED + 1