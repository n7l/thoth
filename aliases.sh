alias tabs='uv run python thoth.py tags | fzf --multi | tr "\n" "," | sed "s/,$//" | xargs -I {} uv run python thoth.py open --tags="[{}]"'
alias tabsn='uv run python thoth.py names | fzf | xargs -I {} uv run python thoth.py open "{}"'