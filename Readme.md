# 公連機器人查榜 v0.1.4

## 運行方式
1. shared_prefs 擺在本目錄
2. 修改 setting.json ( 修改 TOKEN, Owner_id )
3. python bot.py

## 取得 https 解包代理
1. 夜神模擬器 -> Burp suite 監聽全部介面(*:18000)
2. 安裝 local CA certificate (export to der public key)
```
#convert to pem
openssl x509 -inform der -in cert.der -outform pem -out cert.pem

# get first line
openssl x509 -subject_hash_old -in cert.pem
```
3. 將檔案 cert.pem 改名為 `[hash_id].0`, 複製到 /system/etc/security/cacerts, 
(需要 mount /system 為 r,w 權限)

## 取得公連帳號登入Token
可以用 adb root 自行操作或是其他軟體
1. 登入公連一次
2. 打開 root  
3. 複製 /data/data/tw.sonet.princessconnect/shared_prefs/tw.sonet.princessconnect.v2.playerprefs.xml
4. 貼上 /storage/emulated/0/Pictures
5. 關閉 root

## 版本記錄檔
  [Changelog.md](Changelog.md)
