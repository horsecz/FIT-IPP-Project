<?php

/*
*   IPP projekt: cast 1 - parse.php
*   Autor: Dominik Horky
*   VUT FIT, 2021
*/

/************************
*************************
*       "MAIN"
*************************
************************/

ini_set('display_errors', 'stderr');
parseArguments($argc, $argv);

echo("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
$header = false;
$hashtag = -1;
$instr_params = 0;
$line_cnt = 0;
$instr_cnt = 0;
$spaces = 0;

parse();
programEnd();
exit(0);



/************************
*************************
*       FUNKCE
*************************
************************/

/*
*   Parsovani vstupu
*   nacita ze stdin kod, u ktereho overuje spravnost syntaktickou, lexikalni (vc. pritomnosti hlavicky)
*/
function parse() {
    global $header, $line_cnt, $spaces, $hashtag;

    while($line = fgets(STDIN)) {
        $line_cnt++;
        $splitted = explode(' ',  trim($line, "\n")); // nezapomenout na komentare (neoddelene mezerou)
    
        $i = 0;
        while($i < count($splitted) && !strcmp($splitted[$i], ""))
            $i = $i + 1;

        if ($i >= count($splitted))
            $i = $i - 1;

        $spaces = $i;
        switch (strtoupper($splitted[$spaces])) {
            /** instrukce se zadnymi parametry**/
            case 'CREATEFRAME':
            case 'PUSHFRAME':
            case 'POPFRAME':
            case 'RETURN':
            case 'BREAK':
                parseParameters(0, $splitted);
                instructionParseEnd();
                break;

            /** instrukce s 1 parametrem**/
            case 'POPS':
            case 'DEFVAR':
                parseParameters(1, $splitted);
                parseVariable(1, $splitted);
                instructionParseEnd();
                break;
            case 'CALL':
            case 'LABEL':
            case 'JUMP':
                parseParameters(1, $splitted);
                parseLabel(1, $splitted);
                instructionParseEnd();
                break;
            case 'PUSHS':
            case 'WRITE':
            case 'EXIT':
            case 'DPRINT':
                parseParameters(1, $splitted);
                parseSymbol(1, $splitted);
                instructionParseEnd();
                break;

            /** instrukce se 2 parametry **/
            case 'MOVE':
            case 'INT2CHAR':
            case 'STRLEN':
            case 'TYPE':
            case 'NOT':
                parseParameters(2, $splitted);
                parseVariable(1, $splitted);
                parseSymbol(2, $splitted);
                instructionParseEnd();
                break;
            case 'READ':
                parseParameters(2, $splitted);
                parseVariable(1, $splitted);
                parseType(2, $splitted);
                instructionParseEnd();
                break;
            
            /** instrukce se 3 parametry **/
            case 'ADD':
            case 'SUB':
            case 'MUL':
            case 'IDIV':
            case 'LT':
            case 'GT':
            case 'EQ':
            case 'AND':
            case 'OR':
            case 'STRI2INT':
            case 'CONCAT':
            case 'GETCHAR':
            case 'SETCHAR':
                parseParameters(3, $splitted);
                parseVariable(1, $splitted);
                parseSymbol(2, $splitted);
                parseSymbol(3, $splitted);
                instructionParseEnd();
                break;
            case 'JUMPIFEQ':
            case 'JUMPIFNEQ':
                parseParameters(3, $splitted);
                parseLabel(1, $splitted);
                parseSymbol(2, $splitted);
                parseSymbol(3, $splitted);
                break;

            /** ostatni: komentare, hlavicka, neplatne instrukce **/
            case '#':
            case ' ':
            case '\n':
            case '':
                continue 2;
            default:
                if (!$header) {
                    if (!strcmp(".IPPcode21", $splitted[$spaces])) { 
                        $header = true;
                        echo("<program language=\"IPPcode21\">\n");
                    } else {
                        if ($splitted[$spaces][0] != '#') {
                            if ($line_cnt != 1)
                                parseError(22, "Neplatna instrukce '".$splitted[$spaces]."'.");
                            else {
                                checkForHashtag($splitted[$spaces]);
                                if ($hashtag >= 0) {
                                    $header = true;
                                    echo("<program language=\"IPPcode21\">\n");
                                } else
                                parseError(21, "Spatny format hlavicky. Pozadovano '.IPPcode21'");
                            }
                        }
                    }
                } else {
                    if ($splitted[$spaces][0] != '#')
                        parseError(22, "Neplatna instrukce '".$splitted[$spaces]."'.");
                }
                break;
        }
    }

}

/*
*   Kontrola, zda se v parametru nenachazi zacatek komentare bez mezery. 
*/
function parseCommentCheck($string, $param_num) {
    global $hashtag;
    global $instr_params;
    $size = strlen($string);


    if ($hashtag >= 0 && $param_num == $instr_params) {
        return $hashtag;
    }

    return $size;
}

/*
*   Zkontroluje, zda je parametr navestim.
*/
function parseLabel($param_num, $splitted) {
    global $spaces;
    $param_num = $param_num + $spaces;
    $len = parseCommentCheck($splitted[$param_num], $param_num);
    if (preg_match("/^[a-zA-Z#&!?%_*\\$0-9]*$/", $splitted[$param_num])) {
        echo("  <arg".$param_num." type=\"label\">".substr($splitted[$param_num], 0, $len)."</arg".$param_num.">\n");
    }
    else
        parseError(23, "Spatny parametr, ocekavano navesti.");
} 

/*
*   Zkontroluje, zda parametr je symbolem. (tj. promenna nebo nejaka hodnota)
*/
function parseSymbol($param_num, $splitted) {
    global $spaces;
    global $hashtag;
    $param_num = $param_num + $spaces;
    $len = parseCommentCheck($splitted[$param_num], $param_num);

    if (preg_match("/(LF|GF|TF)@[a-zA-Z#&!?%_*$][a-zA-Z#&!?%_*$0-9]*/", $splitted[$param_num])) // je promenna
        echo("  <arg".$param_num." type=\"var\">".substr($splitted[$param_num], 0, $len)."</arg".$param_num.">\n");
    else if (preg_match("/(string|bool|int|nil)@[a-zA-Z#&!?%_*\\$0-9]*/", $splitted[$param_num])) { // je symbol
        $divider = checkForDivider($splitted[$param_num]);
        
        if ($hashtag >= 0)
            $end = $hashtag - $divider - 1;
        else
            $end = $divider - 1 + $len;

        $modified = 0;
        // protoze XML nema rado &, <, >, ...
        $splitted[$param_num] = preg_replace("/&/", "&amp;", $splitted[$param_num], -1, $modified);
        $end = $end + $modified * 5;
        $splitted[$param_num] = preg_replace("/</", "&lt;", $splitted[$param_num], -1, $modified);
        $end = $end + $modified * 4;
        $splitted[$param_num] = preg_replace("/>/", "&gt;", $splitted[$param_num], -1, $modified);
        $end = $end + $modified * 4;

        parseCheckType(substr($splitted[$param_num], 0, $divider), substr($splitted[$param_num], $divider+1, $end));
        echo("  <arg".$param_num." type=\"".substr($splitted[$param_num], 0, $divider)."\">".substr($splitted[$param_num], $divider+1, $end)."</arg".$param_num.">\n");
    }
    else
        parseError(23, "Spatny parametr, ocekavan symbol - promenna ci hodnota.");
} 

/*
*   Kontrola typu, pokud se jedna o arg type="int/string/bool" (symb)
*/
function parseCheckType($type, $value) {
    switch($type) {
        case 'int':
            if (!preg_match("/^[0-9\-]+$/", $value))
                parseError(23, "Neocekavana hodnota - ocekavan INT.");
            break;
        case 'string':
            if (!preg_match("/[a-zA-Z#&*$0-9]*/", $value))
                parseError(23, "Neocekavana hodnota - ocekavan STRING.");
            break;
        case 'bool':
            if (!preg_match("/[true]/", $value) || !preg_match("/[false]/", $value))
                parseError(23, "Neocekavana hodnota - ocekavan BOOL.");
            break;
        case 'nil':
            if (!preg_match("/[nil]/", $value))
                parseError(23, "Neocekavana hodnota - ocekavan NIL.");
            break;
        default:
            break;
    }
}

/*
*   Zkontroluje, zda zadany parametru je datovym typem.
*/
function parseType($param_num, $splitted) {
    global $spaces;
    global $hashtag;
    $param_num = $param_num + $spaces;
    $len = parseCommentCheck($splitted[$param_num], $param_num);
    
    checkForHashtag($splitted[$param_num]);
    $work = $splitted[$param_num];
    if ($hashtag >= 0) {
        $work = substr($splitted[$param_num], 0, $hashtag);
    }

    switch ($work) {
        case 'int':
        case 'string':
        case 'bool':
            echo("  <arg".$param_num." type=\"type\">".substr($splitted[$param_num], 0, $len)."</arg".$param_num.">\n");
            break;
        default:
            parseError(23, "Neplatny typ promenne.");
            break;
    }
}

/*
*   Zkontroluje, zda zadany parametr (cislo $param_num) je promenna.
*/
function parseVariable($param_num, $splitted) {
    global $spaces;
    $param_num = $param_num + $spaces;
    $len = parseCommentCheck($splitted[$param_num], $param_num);
    if (preg_match("/(LF|GF|TF)@[a-zA-Z#&!?%_*$][a-zA-Z#&!?%_*$0-9]*/", $splitted[$param_num]))
        echo("  <arg".$param_num." type=\"var\">".substr($splitted[$param_num], 0, $len)."</arg".$param_num.">\n");
    else
        parseError(23, "Spatny format parametru instrukce / promenne.");
}

/*
*   Zkontroluje spravny pocet parametru pro zadanou instrukci, pokud je spravny, vypise xml kod na vystup.
*   $number je pozadovany pocet parametru
*/
function parseParameters($number, $splitted) {
    global $line_cnt;
    global $instr_cnt;
    global $hashtag;
    global $spaces;
    global $instr_params;
    
    $instr_params = $number;
    $pars = $number + 1;
    $instr_cnt = $instr_cnt + 1;

    if (count($splitted) - $spaces != $pars) {
        if (count($splitted) >= $pars + 1) {
            $i = $pars;
            while (!strcmp($splitted[$i], ""))
                $i = $i + 1;
            if ($splitted[$i][0] == '#' || checkForHashtag($splitted[$number]) >= 0) {
                if (!$hashtag) // hashtag/komentar zakryva cely posledni argument -> argument neni uveden
                    parseError(23, "Spatny pocet argumentu - detekovan zacatek komentare jako prvni znak posledniho argumentu.");
                echo(" <instruction order=\"".$instr_cnt."\" opcode=\"".strtoupper($splitted[$spaces])."\">\n");
                return 0;
            }
        }
        parseError(23, "Spatny pocet parametru instrukce (".$pars."), ocekavano ".$number." parametr/y/u.");
    }

    echo(" <instruction order=\"".$instr_cnt."\" opcode=\"".strtoupper($splitted[$spaces])."\">\n");
}

/*
*   Zkontroluje, zda se ve stringu vyskytuje hashtag (zacina komentar)
*   vrati jeho index nebo zapornou hodnotu, pokud se nevyskytuje nikde
*/
function checkForHashtag($string) {
    $size = strlen($string);
    $i = 0;
    global $hashtag;

    while($i < $size) {
        if ($string[$i] == '#') {
            $hashtag = $i;
            return $i;
        }
        $i = $i + 1;
    }
    
    $hashtag = -1;
    return -1;
}

/*
*   Najde v symbolu @ a vrati jeho pozici / index.
*/
function checkForDivider($string) {
    $size = strlen($string);
    $i = 0;

    while($i < $size) {
        if ($string[$i] == '@') {
            return $i;
        }
        $i = $i + 1;
    }
    
    return -1;
}

/*
*   Vypise XML kod konce instrukce.
*/
function instructionParseEnd() {
    global $hashtag;
    $hashtag = -1;
    echo(" </instruction>\n");
}

/*
*   Funkce, ktera je volana pri chybe parsovani (syntax., lex.)
*   vypise chybovou hlasku a ukonci program
*   vola se pri prvni nalezene chybe
*/
function parseError($exit_code, $text) {
    global $line_cnt;

    if (!strcmp($text, "")) {
        $text = "Syntakticka nebo lexikalni chyba.";
    }
    error_log("\nCHYBA: ".$text." (radek ".$line_cnt.")");
    exit($exit_code);
}

/*
* Parsovani argumentu. Tento skript prijima:
* -> zadne argumenty
* -> 1 argument, muze byt pouze '--help'
*/
function parseArguments($argc, $argv) {
    if ($argc > 1) {
        if ($argc != 2) {
            error_log("CHYBA: Spatny pocet argumentu. Zkus 'parser.php --help'.\n");
            exit(10);
        }
        if ($argv[1] == "--help") {
            echo("Pouziti:\n");
            echo("PHP 7.4 skript typu filtr nacte ze standardniho vstupu zdrojovy kod v IPPcode21, zkontroluje lexikalni a syntaktickou spravnost kodu a vypise na starndardni vystup XML reprezentaci programu dle specifikace zadani.\n");
            echo("\nSkript pracuje s temito parametry:\n--help\t\tvypise napovedu ke skriptu\n");
            exit(0);
        } else {
            error_log("CHYBA: Spatny argument. Zkus 'parser.php --help'.\n");
            exit(10); 
        }
    }
}

/*
* Konec programu
* vygeneruje konec XML kodu a zkontroluje pritomnost hlavicky
*/
function programEnd() {
    global $header;
    if (!$header) {
        error_log("\nCHYBA: Zadany vstup neobsahuje hlavicku '.IPPcode21'");
        exit(21);
    }
    echo("</program>\n");
}
?>