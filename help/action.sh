sudo apt-get install jq

obj="{"
for dir in Apps/*; do
    result=$(cat ./$dir/appfile.json)
    tagline=$(echo "$result" | jq .tagline)
    title=$(echo "$result" | jq .title)
    overview=$(echo "$result" | jq .overview)
    #tips=`echo "$result" | jq .tops.before_install[].content`
    content="{\"tagline\": ${tagline} , \"overview\":${overview} },"
    obj="${obj} ${title} : ${content}"
done
obj=${obj%?}
obj="${obj} }"
data=$(echo "$obj" | jq .)
echo "$data" > ./CasaOS-i18n/back-end/en_us.json
