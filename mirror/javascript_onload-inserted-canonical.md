# [https://crawler-test.com/javascript/onload-inserted-canonical](https://crawler-test.com/javascript/onload-inserted-canonical)

**Source URL:** https://crawler-test.com/javascript/onload-inserted-canonical

---

<html><head> <title>On click added canonical</title> <link rel="canonical" href="/onload-added-canonical.html"></head> <body> <script type="text/javascript"> function addCanonical() { var tag = document.createElement('link'); tag.rel = 'canonical'; tag.href = '/onload-added-canonical.html'; document.getElementsByTagName('head')[0].appendChild(tag); } window.onload = addCanonical; </script>  </body></html>