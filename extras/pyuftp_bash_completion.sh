
_pyuftp()
{
  local cur prev commands global_opts opts
  COMPREPLY=()
  cur=`_get_cword`
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  commands="authenticate checksum cp find info ls mkdir rm share"
  global_opts="--help --verbose --token --user --password --identity --help"


  # parsing for uftp command word (2nd word in commandline.
  # uftp <command> [OPTIONS] <args>)
  if [ $COMP_CWORD -eq 1 ]; then
    COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
    return 0
  fi

  # looking for arguments matching to command
  case "${COMP_WORDS[1]}" in
    authenticate)
    opts="$global_opts "
    ;;
    checksum)
    opts="$global_opts --algorithm"
    ;;
    cp)
    opts="$global_opts --archive --bytes --recurse"
    ;;
    find)
    opts="$global_opts "
    ;;
    info)
    opts="$global_opts --raw"
    ;;
    ls)
    opts="$global_opts "
    ;;
    mkdir)
    opts="$global_opts "
    ;;
    rm)
    opts="$global_opts "
    ;;
    share)
    opts="$global_opts --access --delete --lifetime --list --one --server --write"
    ;;

  esac

  COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
  
  _filedir

}

complete -o filenames -F _pyuftp pyuftp
