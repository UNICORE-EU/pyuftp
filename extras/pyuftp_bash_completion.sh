
_pyuftp()
{
  local cur prev commands global_opts opts
  COMPREPLY=()
  cur=`_get_cword`
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  commands="authenticate checksum cp find info issue-token ls mkdir rcp rm share"
  global_opts="--auth --help --identity --oidc --password --user --verbose"


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
    opts="$global_opts --archive --bytes --compress --encrypt --recurse --resume --show --streams --threads"
    ;;
    find)
    opts="$global_opts --files --pattern --recurse"
    ;;
    info)
    opts="$global_opts --connect --raw"
    ;;
    issue-token)
    opts="$global_opts --inspect --lifetime --limited --renewable"
    ;;
    ls)
    opts="$global_opts "
    ;;
    mkdir)
    opts="$global_opts "
    ;;
    rcp)
    opts="$global_opts --bytes --compress --encrypt --one --server --streams"
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
