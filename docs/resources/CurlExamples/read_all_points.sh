## Read all points
curl -X "POST" "http://localhost/haystack/read" \
     -H 'Accept: application/json' \
     -H 'Content-Type: text/zinc' \
     -d $'ver:"2.0" 
filter,limit 
"point",1000
'
