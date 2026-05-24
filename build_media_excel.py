# -*- coding: utf-8 -*-
"""按国家汇总主流媒体网站，验证可访问后导出 Excel。"""
import concurrent.futures
import time
from urllib.parse import urlparse

import pandas as pd
import requests

# (网站, 媒体, 文种, 国家中文名)
MEDIA_DATA = [
    # 亚洲
    ("https://www.people.com.cn", "人民网", "中文", "中国"),
    ("https://www.xinhuanet.com", "新华网", "中文", "中国"),
    ("https://news.sina.com.cn", "新浪新闻", "中文", "中国"),
    ("https://www.163.com", "网易新闻", "中文", "中国"),
    ("https://news.qq.com", "腾讯新闻", "中文", "中国"),
    ("https://www.asahi.com", "朝日新闻", "日语", "日本"),
    ("https://www.nikkei.com", "日本经济新闻", "日语", "日本"),
    ("https://news.yahoo.co.jp", "Yahoo!ニュース", "日语", "日本"),
    ("https://www.chosun.com", "朝鲜日报", "韩语", "韩国"),
    ("https://www.joongang.co.kr", "中央日报", "韩语", "韩国"),
    ("https://www.naver.com", "Naver", "韩语", "韩国"),
    ("https://www.yonhapnews.co.kr", "韩联社", "韩语", "韩国"),
    ("https://www.bbc.com/hindi", "BBC Hindi", "印地语", "印度"),
    ("https://timesofindia.indiatimes.com", "印度时报", "英语", "印度"),
    ("https://www.thehindu.com", "印度教徒报", "英语", "印度"),
    ("https://www.hindustantimes.com", "印度斯坦时报", "英语", "印度"),
    ("https://www.ndtv.com", "NDTV", "英语", "印度"),
    ("https://www.detik.com", "Detik", "印尼语", "印度尼西亚"),
    ("https://www.kompas.com", "Kompas", "印尼语", "印度尼西亚"),
    ("https://www.cnnindonesia.com", "CNN Indonesia", "印尼语", "印度尼西亚"),
    ("https://www.bangkokpost.com", "Bangkok Post", "英语", "泰国"),
    ("https://www.thairath.co.th", "Thairath", "泰语", "泰国"),
    ("https://www.bernama.com", "Bernama", "马来语/英语", "马来西亚"),
    ("https://www.straitstimes.com", "海峡时报", "英语", "新加坡"),
    ("https://www.channelnewsasia.com", "CNA", "英语", "新加坡"),
    ("https://www.rappler.com", "Rappler", "英语", "菲律宾"),
    ("https://www.inquirer.net", "Philippine Daily Inquirer", "英语", "菲律宾"),
    ("https://vnexpress.net", "VnExpress", "越南语", "越南"),
    ("https://tuoitre.vn", "Tuoi Tre", "越南语", "越南"),
    ("https://www.phnompenhpost.com", "Phnom Penh Post", "英语", "柬埔寨"),
    ("https://www.thestar.com.my", "The Star", "英语", "马来西亚"),
    ("https://www.dawn.com", "Dawn", "英语", "巴基斯坦"),
    ("https://tribune.com.pk", "Express Tribune", "英语", "巴基斯坦"),
    ("https://www.bdnews24.com", "bdnews24", "孟加拉语/英语", "孟加拉国"),
    ("https://www.dailymirror.lk", "Daily Mirror", "英语", "斯里兰卡"),
    ("https://www.tehrantimes.com", "Tehran Times", "英语", "伊朗"),
    ("https://www.isna.ir", "ISNA", "波斯语", "伊朗"),
    ("https://www.aljazeera.com", "半岛电视台", "英语/阿拉伯语", "卡塔尔"),
    ("https://www.arabnews.com", "Arab News", "英语", "沙特阿拉伯"),
    ("https://www.saudigazette.com.sa", "Saudi Gazette", "英语", "沙特阿拉伯"),
    ("https://gulfnews.com", "Gulf News", "英语", "阿联酋"),
    ("https://www.thenationalnews.com", "The National", "英语", "阿联酋"),
    ("https://www.haaretz.com", "Haaretz", "英语/希伯来语", "以色列"),
    ("https://www.jpost.com", "Jerusalem Post", "英语", "以色列"),
    ("https://www.ynet.co.il", "Ynet", "希伯来语", "以色列"),
    ("https://www.hurriyet.com.tr", "Hürriyet", "土耳其语", "土耳其"),
    ("https://www.sabah.com.tr", "Sabah", "土耳其语", "土耳其"),
    ("https://www.trtworld.com", "TRT World", "英语", "土耳其"),
    # 欧洲
    ("https://www.bbc.com", "BBC", "英语", "英国"),
    ("https://www.theguardian.com", "卫报", "英语", "英国"),
    ("https://www.telegraph.co.uk", "每日电讯报", "英语", "英国"),
    ("https://www.dailymail.co.uk", "每日邮报", "英语", "英国"),
    ("https://www.lemonde.fr", "世界报", "法语", "法国"),
    ("https://www.lefigaro.fr", "费加罗报", "法语", "法国"),
    ("https://www.france24.com", "France 24", "法语/英语", "法国"),
    ("https://www.spiegel.de", "明镜周刊", "德语", "德国"),
    ("https://www.zeit.de", "时代周报", "德语", "德国"),
    ("https://www.faz.net", "法兰克福汇报", "德语", "德国"),
    ("https://www.bild.de", "图片报", "德语", "德国"),
    ("https://www.dw.com", "德国之声", "德语/多语", "德国"),
    ("https://elpais.com", "国家报", "西班牙语", "西班牙"),
    ("https://www.elmundo.es", "世界报(西)", "西班牙语", "西班牙"),
    ("https://www.corriere.it", "晚邮报", "意大利语", "意大利"),
    ("https://www.repubblica.it", "共和国报", "意大利语", "意大利"),
    ("https://www.ansa.it", "安莎社", "意大利语", "意大利"),
    ("https://www.nrc.nl", "新鹿特丹商报", "荷兰语", "荷兰"),
    ("https://www.volkskrant.nl", "人民报", "荷兰语", "荷兰"),
    ("https://www.rtlnieuws.nl", "RTL Nieuws", "荷兰语", "荷兰"),
    ("https://www.standaard.be", "标准报", "荷兰语", "比利时"),
    ("https://www.lesoir.be", "晚报", "法语", "比利时"),
    ("https://www.nzz.ch", "新苏黎世报", "德语", "瑞士"),
    ("https://www.tagesanzeiger.ch", "每日导报", "德语", "瑞士"),
    ("https://www.aftonbladet.se", "晚报", "瑞典语", "瑞典"),
    ("https://www.dn.se", "每日新闻", "瑞典语", "瑞典"),
    ("https://www.vg.no", "Verdens Gang", "挪威语", "挪威"),
    ("https://www.aftenposten.no", "晚邮报", "挪威语", "挪威"),
    ("https://www.dr.dk", "丹麦广播", "丹麦语", "丹麦"),
    ("https://www.politiken.dk", "政治报", "丹麦语", "丹麦"),
    ("https://www.hs.fi", "赫尔辛基报", "芬兰语", "芬兰"),
    ("https://www.yle.fi", "芬兰广播", "芬兰语", "芬兰"),
    ("https://www.irishtimes.com", "爱尔兰时报", "英语", "爱尔兰"),
    ("https://www.rte.ie", "爱尔兰国家电视台", "英语", "爱尔兰"),
    ("https://www.publico.pt", "公众报", "葡萄牙语", "葡萄牙"),
    ("https://expresso.pt", "快报", "葡萄牙语", "葡萄牙"),
    ("https://www.ekathimerini.com", "希腊每日报", "英语", "希腊"),
    ("https://www.kathimerini.gr", "每日报", "希腊语", "希腊"),
    ("https://www.gazeta.ru", "Gazeta.ru", "俄语", "俄罗斯"),
    ("https://www.kommersant.ru", "生意人报", "俄语", "俄罗斯"),
    ("https://www.rbc.ru", "RBC", "俄语", "俄罗斯"),
    ("https://www.rt.com", "RT", "英语/俄语", "俄罗斯"),
    ("https://www.pravda.com.ua", "真理报(乌)", "乌克兰语", "乌克兰"),
    ("https://www.kyivpost.com", "基辅邮报", "英语", "乌克兰"),
    ("https://www.onet.pl", "Onet", "波兰语", "波兰"),
    ("https://www.rp.pl", "共和国报", "波兰语", "波兰"),
    ("https://www.idnes.cz", "iDNES", "捷克语", "捷克"),
    ("https://www.novinky.cz", "Novinky", "捷克语", "捷克"),
    ("https://index.hu", "Index", "匈牙利语", "匈牙利"),
    ("https://www.origo.hu", "Origo", "匈牙利语", "匈牙利"),
    ("https://www.digi24.ro", "Digi24", "罗马尼亚语", "罗马尼亚"),
    ("https://www.hotnews.ro", "HotNews", "罗马尼亚语", "罗马尼亚"),
    ("https://www.novinite.com", "Novinite", "英语", "保加利亚"),
    ("https://www.sme.sk", "SME", "斯洛伐克语", "斯洛伐克"),
    ("https://www.delo.si", "Delo", "斯洛文尼亚语", "斯洛文尼亚"),
    ("https://www.lrt.lt", "LRT", "立陶宛语", "立陶宛"),
    ("https://www.delfi.lv", "Delfi", "拉脱维亚语", "拉脱维亚"),
    ("https://www.err.ee", "ERR", "爱沙尼亚语", "爱沙尼亚"),
    ("https://www.hln.be", "Het Laatste Nieuws", "荷兰语", "比利时"),
    ("https://www.kurier.at", "Kurier", "德语", "奥地利"),
    ("https://www.derstandard.at", "标准报", "德语", "奥地利"),
    # 北美
    ("https://www.nytimes.com", "纽约时报", "英语", "美国"),
    ("https://www.cnn.com", "CNN", "英语", "美国"),
    ("https://www.foxnews.com", "福克斯新闻", "英语", "美国"),
    ("https://www.washingtonpost.com", "华盛顿邮报", "英语", "美国"),
    ("https://www.usatoday.com", "今日美国", "英语", "美国"),
    ("https://www.wsj.com", "华尔街日报", "英语", "美国"),
    ("https://www.latimes.com", "洛杉矶时报", "英语", "美国"),
    ("https://www.cbc.ca", "加拿大广播公司", "英语/法语", "加拿大"),
    ("https://www.theglobeandmail.com", "环球邮报", "英语", "加拿大"),
    ("https://www.lapresse.ca", "La Presse", "法语", "加拿大"),
    ("https://www.eluniversal.com.mx", "宇宙报", "西班牙语", "墨西哥"),
    ("https://www.reforma.com", "Reforma", "西班牙语", "墨西哥"),
    ("https://www.jornada.com.mx", "La Jornada", "西班牙语", "墨西哥"),
    # 中美洲与加勒比
    ("https://www.prensa.com", "La Prensa", "西班牙语", "巴拿马"),
    ("https://www.laprensa.hn", "La Prensa", "西班牙语", "洪都拉斯"),
    ("https://www.elfinanciero.com", "金融报", "西班牙语", "哥斯达黎加"),
    ("https://www.laprensa.com.ni", "La Prensa", "西班牙语", "尼加拉瓜"),
    ("https://www.elnuevoherald.com", "迈阿密先驱报", "西班牙语", "古巴"),
    ("https://www.jamaica-gleaner.com", "Gleaner", "英语", "牙买加"),
    ("https://www.trinidadexpress.com", "Express", "英语", "特立尼达和多巴哥"),
    # 南美
    ("https://www.globo.com", "Globo", "葡萄牙语", "巴西"),
    ("https://www.uol.com.br", "UOL", "葡萄牙语", "巴西"),
    ("https://www.folha.uol.com.br", "圣保罗页报", "葡萄牙语", "巴西"),
    ("https://www.clarin.com", "号角报", "西班牙语", "阿根廷"),
    ("https://www.lanacion.com.ar", "民族报", "西班牙语", "阿根廷"),
    ("https://www.emol.com", "Emol", "西班牙语", "智利"),
    ("https://www.latercera.com", "第三报", "西班牙语", "智利"),
    ("https://www.elcomercio.pe", "商报", "西班牙语", "秘鲁"),
    ("https://www.eluniverso.com", "宇宙报", "西班牙语", "厄瓜多尔"),
    ("https://www.eltiempo.com", "时代报", "西班牙语", "哥伦比亚"),
    ("https://www.semana.com", "Semana", "西班牙语", "哥伦比亚"),
    ("https://www.elpais.com.uy", "国家报", "西班牙语", "乌拉圭"),
    ("https://www.abc.com.py", "ABC Color", "西班牙语", "巴拉圭"),
    ("https://www.lostiempos.com", "Los Tiempos", "西班牙语", "玻利维亚"),
    ("https://www.el-nacional.com", "El Nacional", "西班牙语", "委内瑞拉"),
    # 非洲
    ("https://www.news24.com", "News24", "英语", "南非"),
    ("https://www.dailymaverick.co.za", "Daily Maverick", "英语", "南非"),
    ("https://www.premiumtimesng.com", "Premium Times", "英语", "尼日利亚"),
    ("https://punchng.com", "Punch", "英语", "尼日利亚"),
    ("https://www.theeastafrican.co.ke", "East African", "英语", "肯尼亚"),
    ("https://www.nation.africa", "Daily Nation", "英语", "肯尼亚"),
    ("https://www.egypttoday.com", "Egypt Today", "英语", "埃及"),
    ("https://www.youm7.com", "Youm7", "阿拉伯语", "埃及"),
    ("https://www.senenews.com", "Senenews", "法语", "塞内加尔"),
    ("https://www.jeuneafrique.com", "Jeune Afrique", "法语", "科特迪瓦"),
    ("https://www.hespress.com", "Hespress", "阿拉伯语", "摩洛哥"),
    ("https://www.le360.ma", "Le360", "法语/阿拉伯语", "摩洛哥"),
    ("https://www.ethiopianreporter.com", "Reporter", "英语", "埃塞俄比亚"),
    ("https://www.newtimes.co.rw", "New Times", "英语", "卢旺达"),
    ("https://www.monitor.co.ug", "Daily Monitor", "英语", "乌干达"),
    ("https://www.thecitizen.co.tz", "The Citizen", "英语", "坦桑尼亚"),
    ("https://www.ghanaweb.com", "GhanaWeb", "英语", "加纳"),
    ("https://www.liberianobserver.com", "Observer", "英语", "利比里亚"),
    ("https://www.cameroon-tribune.cm", "Cameroon Tribune", "英语/法语", "喀麦隆"),
    ("https://www.algerie360.com", "Algérie 360", "法语/阿拉伯语", "阿尔及利亚"),
    ("https://www.tunisienumerique.com", "Tunisie Numérique", "法语/阿拉伯语", "突尼斯"),
    # 大洋洲
    ("https://www.abc.net.au", "澳大利亚广播公司", "英语", "澳大利亚"),
    ("https://www.smh.com.au", "悉尼先驱晨报", "英语", "澳大利亚"),
    ("https://www.theaustralian.com.au", "澳大利亚人报", "英语", "澳大利亚"),
    ("https://www.nzherald.co.nz", "新西兰先驱报", "英语", "新西兰"),
    ("https://www.stuff.co.nz", "Stuff", "英语", "新西兰"),
    ("https://www.fijitimes.com.fj", "Fiji Times", "英语", "斐济"),
    ("https://www.postcourier.com.pg", "Post-Courier", "英语", "巴布亚新几内亚"),
    # 中亚与高加索
    ("https://www.kazinform.kz", "Kazinform", "哈萨克语/俄语", "哈萨克斯坦"),
    ("https://www.trend.az", "Trend", "阿塞拜疆语/英语", "阿塞拜疆"),
    ("https://www.1tv.ge", "Georgian Public Broadcaster", "格鲁吉亚语", "格鲁吉亚"),
    ("https://www.armenpress.am", "Armenpress", "亚美尼亚语", "亚美尼亚"),
    ("https://www.uza.uz", "UzA", "乌兹别克语", "乌兹别克斯坦"),
    # 补充小国
    ("https://www.icelandreview.com", "Iceland Review", "英语", "冰岛"),
    ("https://www.mbl.is", "Morgunblaðið", "冰岛语", "冰岛"),
    ("https://www.maldivesindependent.com", "Maldives Independent", "英语", "马尔代夫"),
    ("https://www.montsame.mn", "Montsame", "蒙古语", "蒙古"),
    ("https://www.tap.info.tn", "TAP", "阿拉伯语/法语", "突尼斯"),
    ("https://www.vientianetimes.org.la", "Vientiane Times", "英语", "老挝"),
    ("https://www.bt.com.bn", "Borneo Bulletin", "英语", "文莱"),
    ("https://www.tatoli.tl", "Tatoli", "葡萄牙语/德顿语", "东帝汶"),
    ("https://www.nepalitimes.com", "Nepali Times", "英语", "尼泊尔"),
    ("https://www.kathmandupost.com", "Kathmandu Post", "英语", "尼泊尔"),
    ("https://kuenselonline.com", "Kuensel", "英语", "不丹"),
    ("https://www.mizzima.com", "Mizzima", "英语", "缅甸"),
    ("https://www.globaltimes.cn", "环球时报", "英语", "中国"),
    ("https://www.cna.com.tw", "中央社", "中文", "中国台湾"),
    ("https://www.taiwannews.com.tw", "Taiwan News", "英语", "中国台湾"),
    ("https://www.hongkongfp.com", "Hong Kong Free Press", "英语", "中国香港"),
    ("https://www.scmp.com", "南华早报", "英语", "中国香港"),
    ("https://www.macaubusiness.com", "Macau Business", "英语", "中国澳门"),
    # 补充替代与更多国家
    ("https://edition.cnn.com", "CNN International", "英语", "美国"),
    ("https://www.reuters.com", "路透社", "英语", "英国"),
    ("https://apnews.com", "美联社", "英语", "美国"),
    ("https://www.afp.com", "法新社", "法语/英语", "法国"),
    ("https://www.tagesschau.de", "德国电视一台新闻", "德语", "德国"),
    ("https://www.nos.nl", "NOS", "荷兰语", "荷兰"),
    ("https://www.rtp.pt", "RTP", "葡萄牙语", "葡萄牙"),
    ("https://www.antena3.com", "Antena 3", "西班牙语", "西班牙"),
    ("https://www.lanacion.cl", "La Nación", "西班牙语", "智利"),
    ("https://www.lanacion.com.py", "La Nación", "西班牙语", "巴拉圭"),
    ("https://www.laprensa.com.bo", "La Prensa", "西班牙语", "玻利维亚"),
    ("https://www.laprensagrafica.com", "La Prensa Gráfica", "西班牙语", "萨尔瓦多"),
    ("https://www.prensalibre.com", "Prensa Libre", "西班牙语", "危地马拉"),
    ("https://www.laprensa.hn", "La Prensa", "西班牙语", "洪都拉斯"),
    ("https://www.elnuevodiario.com.ni", "El Nuevo Diario", "西班牙语", "尼加拉瓜"),
    ("https://www.granma.cu", "Granma", "西班牙语", "古巴"),
    ("https://www.haitilibre.com", "Haiti Libre", "法语", "海地"),
    ("https://www.dominicantoday.com", "Dominican Today", "英语", "多米尼加"),
    ("https://www.listindiario.com", "Listín Diario", "西班牙语", "多米尼加"),
    ("https://www.kuwaittimes.com", "Kuwait Times", "英语", "科威特"),
    ("https://www.gulf-times.com", "Gulf Times", "英语", "卡塔尔"),
    ("https://www.bna.bh", "BNA", "阿拉伯语/英语", "巴林"),
    ("https://www.timesofoman.com", "Times of Oman", "英语", "阿曼"),
    ("https://www.jordantimes.com", "Jordan Times", "英语", "约旦"),
    ("https://www.nna-leb.gov.lb", "NNA", "阿拉伯语", "黎巴嫩"),
    ("https://www.lbcgroup.tv", "LBCI", "阿拉伯语", "黎巴嫩"),
    ("https://www.syria-tv.net", "Syria TV", "阿拉伯语", "叙利亚"),
    ("https://www.iraqinews.com", "Iraqi News", "英语", "伊拉克"),
    ("https://www.ekurd.net", "Ekurd", "英语/库尔德语", "伊拉克"),
    ("https://www.tasnimnews.com", "Tasnim", "波斯语", "伊朗"),
    ("https://www.azernews.az", "AzerNews", "英语", "阿塞拜疆"),
    ("https://en.armradio.am", "Public Radio of Armenia", "英语", "亚美尼亚"),
    ("https://www.interpressnews.ge", "Interpressnews", "格鲁吉亚语", "格鲁吉亚"),
    ("https://www.moldpres.md", "Moldpres", "罗马尼亚语", "摩尔多瓦"),
    ("https://www.belta.by", "Belta", "俄语", "白俄罗斯"),
    ("https://www.baltictimes.com", "Baltic Times", "英语", "拉脱维亚"),
    ("https://www.lrytas.lt", "Lrytas", "立陶宛语", "立陶宛"),
    ("https://www.madagascar-tribune.com", "Madagascar Tribune", "法语", "马达加斯加"),
    ("https://www.namibian.com.na", "Namibian", "英语", "纳米比亚"),
    ("https://www.zambiawatchdog.com", "Zambia Watchdog", "英语", "赞比亚"),
    ("https://www.herald.co.zw", "Herald", "英语", "津巴布韦"),
    ("https://www.mg.co.za", "Mail & Guardian", "英语", "南非"),
    ("https://www.dzairdaily.com", "Dzair Daily", "法语/阿拉伯语", "阿尔及利亚"),
    ("https://www.businessday.ng", "Business Day", "英语", "尼日利亚"),
    ("https://www.standardmedia.co.ke", "Standard", "英语", "肯尼亚"),
    ("https://www.malawitimes.com", "Malawi Times", "英语", "马拉维"),
    ("https://www.times.mw", "Times", "英语", "马拉维"),
    ("https://www.sierra-leone.org", "Sierra Leone Web", "英语", "塞拉利昂"),
    ("https://www.liberianobserver.com", "Observer", "英语", "利比里亚"),
    ("https://www.guineenews.org", "Guinéenews", "法语", "几内亚"),
    ("https://www.africaintelligence.com", "Africa Intelligence", "法语", "马里"),
    ("https://www.sudantribune.com", "Sudan Tribune", "英语", "苏丹"),
    ("https://www.southsudannewsagency.com", "South Sudan News", "英语", "南苏丹"),
    ("https://www.middleeasteye.net", "Middle East Eye", "英语", "也门"),
    ("https://www.yemenonline.info", "Yemen Online", "阿拉伯语/英语", "也门"),
    ("https://www.solomonstarnews.com", "Solomon Star", "英语", "所罗门群岛"),
    ("https://www.vanuatudaily.com", "Vanuatu Daily", "英语", "瓦努阿图"),
    ("https://www.samoaobserver.ws", "Samoa Observer", "英语", "萨摩亚"),
    ("https://www.tongatimes.to", "Tonga Times", "英语", "汤加"),
    ("https://www.rnzi.com", "RNZ Pacific", "英语", "新西兰"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
}


def normalize_url(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")


def check_url(item: tuple) -> dict:
    url, media, lang, country = item
    url = normalize_url(url)
    status = "可访问"
    note = ""
    try:
        r = requests.get(
            url,
            headers=HEADERS,
            timeout=15,
            allow_redirects=True,
            stream=True,
        )
        code = r.status_code
        r.close()
        if code in (401, 403, 429, 444):
            status = "受限"
            note = f"HTTP {code}（反爬/订阅墙，站点可响应）"
        elif code >= 400:
            status = "不可访问"
            note = f"HTTP {code}"
    except requests.exceptions.SSLError:
        status = "受限"
        note = "SSL/证书问题（站点可能存在）"
    except requests.exceptions.Timeout:
        status = "超时"
        note = "连接超时"
    except requests.exceptions.ConnectionError as e:
        status = "不可访问"
        note = str(e)[:80]
    except Exception as e:
        status = "不可访问"
        note = str(e)[:80]

    return {
        "网站": url,
        "媒体": media,
        "文种": lang,
        "国家": country,
        "可访问性": status,
        "备注": note,
    }


def dedupe_by_country_media(rows: list) -> list:
    seen = set()
    out = []
    for row in rows:
        key = (row[3], row[1], urlparse(normalize_url(row[0])).netloc)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def main():
    raw = dedupe_by_country_media(MEDIA_DATA)
    print(f"共 {len(raw)} 条记录，开始检测可访问性…")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        futures = [ex.submit(check_url, item) for item in raw]
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            results.append(fut.result())
            if i % 20 == 0:
                print(f"  已检测 {i}/{len(raw)}")

    # 优先保留可访问与受限（付费墙等仍算可打开）
    ok_status = {"可访问", "受限"}
    accessible = [r for r in results if r["可访问性"] in ok_status]
    failed = [r for r in results if r["可访问性"] not in ok_status]

    accessible.sort(key=lambda x: (x["国家"], x["媒体"]))
    failed.sort(key=lambda x: (x["国家"], x["媒体"]))

    df_main = pd.DataFrame(accessible)[["网站", "媒体", "文种", "国家"]]
    df_all = pd.DataFrame(results)[["网站", "媒体", "文种", "国家", "可访问性", "备注"]]

    out_path = "各国主流媒体网站.xlsx"
    df_main = df_main.sort_values(["国家", "媒体"], ignore_index=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df_main.to_excel(writer, sheet_name="主流媒体列表", index=False)
        df_all.sort_values(["国家", "媒体"]).to_excel(
            writer, sheet_name="全部检测记录", index=False
        )
        if failed:
            pd.DataFrame(failed)[["网站", "媒体", "文种", "国家", "可访问性", "备注"]].to_excel(
                writer, sheet_name="未通过检测", index=False
            )

    print(f"\n完成：{out_path}")
    print(f"  可访问/受限（已列入主表）: {len(accessible)}")
    print(f"  未通过: {len(failed)}")
    if failed:
        print("  未通过示例:")
        for r in failed[:8]:
            print(f"    - {r['媒体']} ({r['国家']}): {r['可访问性']} {r['备注']}")


if __name__ == "__main__":
    main()
