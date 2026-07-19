(function(){
  var DATA = {"domesticLabels": ["B300", "B200", "H200", "H100 80G", "H800", "A100 80G", "L40S", "L20", "L4", "RTX 5090", "RTX 4090", "昇腾 910C", "昇腾 910B", "昇腾 950PR", "寒武纪 MLU370-X8", "寒武纪 MLU590", "海光 DCU K100", "海光 DCU Z100", "壁仞 BR100", "摩尔线程 MTT S4000", "摩尔线程 MTT S5000"], "domesticValues": [28.0, 13.0, 9.4, 7.75, 6.9, 2.5, 1.2, 4.23, 3.25, 1.2, 0.78, 6.2, 1.5, 0, 3.49, 0, 1.21, 0, 0.6, 0.68, 0], "domesticRatios": ["96.9%", "49.7%", "54.8%", "66.3%", "海外缺口", "42.9%", "31.0%", "云折", "云折", "31.0%", "28.9%", "海外缺口", "海外缺口", "价格待补", "云折", "价格待补", "云折", "价格待补", "云折", "云折", "价格待补"], "domesticKinds": ["公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "云价折算", "云价折算", "公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "价格待补", "云价折算", "价格待补", "云价折算", "价格待补", "云价折算", "云价折算", "价格待补"], "overseasLabels": ["GB300", "GB200", "B300", "B200", "H200", "H100 80G", "A100 80G", "L40S", "L4", "RTX 5090", "RTX 4090"], "overseasValues": [52.05, 51.82, 33.98, 24.17, 16.42, 12.55, 8.37, 5.09, 2.51, 2.93, 2.31], "tokenLabels": ["OpenAI\\nGPT-5.5", "OpenAI\\nGPT-5.4", "OpenAI\\nGPT-5.4 mini", "OpenAI\\no4 Mini", "Anthropic\\nClaude Fable 5", "Anthropic\\nClaude Opus 4.8", "Anthropic\\nClaude Sonnet 5", "Anthropic\\nClaude Haiku 4.5", "Google\\nGemini 3.5 Flash", "Google\\nGemini 3.1 Pro Preview", "Google\\nGemini 3.1 Flash-Lite", "Mistral\\nMistral Medium 3.5", "Mistral\\nMistral Large 3", "Mistral\\nMistral Small 4", "Cohere\\nCommand A+", "Cohere\\nCommand R+", "xAI Grok\\nGrok 4.5", "xAI Grok\\nGrok 4.3", "xAI Grok\\nGrok 4.20", "Meta Llama\\nLlama 4 Maverick", "Meta Llama\\nLlama 4 Scout", "DeepSeek\\nDeepSeek-V4-Pro", "DeepSeek\\nDeepSeek-V4-Flash", "阿里云/通义千问\\nQwen3.7-Max", "阿里云/通义千问\\nQwen3.7-Plus", "火山方舟/豆包\\nDoubao-Seed 2.1 Pro", "火山方舟/豆包\\nDoubao-Seed 2.1 Turbo", "火山方舟/豆包\\nDoubao-Seed 2.0 Pro", "火山方舟/豆包\\nDoubao-Seed-Evolving", "腾讯混元\\nHunyuan-Hy3", "腾讯混元\\nHunyuan-role-latest", "腾讯混元\\nHunyuan-A13B", "智谱 GLM / Z.ai\\nGLM-5.2", "智谱 GLM / Z.ai\\nGLM-5.1 Pro", "百度文心\\nERNIE 5.1", "百度文心\\nERNIE-4.5-Turbo", "Kimi / Moonshot\\nKimi K3", "Kimi / Moonshot\\nKimi K2.7 Code", "Kimi / Moonshot\\nKimi K2.6", "MiniMax\\nMiniMax-M3 标准层 ≤512K", "MiniMax\\nMiniMax-M3 标准层 >512K", "讯飞星火\\nSpark X2", "讯飞星火\\nSpark Max", "百川智能\\nBaichuan-M3-Plus", "百川智能\\nBaichuan-M3", "零一万物\\nYi-Lightning", "零一万物\\nYi-Large", "阶跃星辰\\nStep 3.5 Flash", "阶跃星辰\\nStep-R1-V-Mini", "商汤日日新\\nSenseNova-V6.5-Pro", "商汤日日新\\nSenseNova-V6.5-Turbo", "昆仑万维天工\\nSkyClaw-v1.0", "昆仑万维天工\\nSkyClaw-v1.0-lite"], "tokenOfficialIn": [33.95, 16.97, 5.09, 7.47, 67.89, 33.95, 13.58, 6.79, 10.18, 13.58, 1.7, 13.58, 3.39, 0.68, 16.97, 16.97, 13.58, 8.49, 13.58, 1.36, 0.68, 3.0, 1.0, 12.0, 2.0, 6.0, 3.0, 3.2, 6.0, 1.0, 2.4, 0.5, 8.0, 6.0, 4.0, 0.8, 20.0, 6.5, 6.5, 2.1, 4.2, 1.0, 21.0, 5.0, 10.0, 0.99, 20.0, 0.7, 2.5, 3.0, 1.5, 0.5, 0.3], "tokenOverseasIn": [33.95, 16.97, 5.09, 7.47, 67.89, 33.95, 13.58, 6.79, 10.18, 13.58, 1.7, 10.18, 3.39, 1.02, 16.97, 16.97, 13.58, 8.49, 8.49, 1.36, 0.68, 11.81, 0.95, 8.49, 2.17, 6.0, 3.0, 3.2, 6.0, 1.0, 2.4, 0.95, 6.14, 9.5, 4.0, 2.85, 20.37, 4.88, 4.48, 2.04, 4.2, 1.0, 21.0, 5.0, 10.0, 0.99, 20.0, 0.7, 2.5, 3.0, 1.5, 0.5, 0.3], "tokenDomesticIn": [33.95, 16.97, 5.09, 7.47, 67.89, 33.95, 13.58, 6.79, 10.18, 13.58, 1.7, 13.58, 3.39, 0.68, 16.97, 16.97, 13.58, 8.49, 13.58, 1.36, 0.68, 12.0, 1.0, 12.0, 2.0, 6.0, 3.0, 1.5, 6.0, 1.0, 2.4, 1.0, 8.0, 6.0, 4.0, 0.8, 20.0, 6.5, 6.5, 2.1, 4.2, 1.0, 21.0, 5.0, 10.0, 0.99, 20.0, 0.7, 2.5, 3.0, 1.5, 0.5, 0.3], "tokenOfficialOut": [203.68, 101.84, 30.55, 29.87, 339.46, 169.73, 67.89, 33.95, 61.1, 81.47, 10.18, 50.92, 10.18, 2.04, 67.89, 67.89, 40.74, 16.97, 40.74, 5.43, 2.04, 6.0, 2.0, 36.0, 8.0, 30.0, 15.0, 16.0, 30.0, 4.0, 9.6, 2.0, 28.0, 24.0, 18.0, 3.2, 100.0, 27.0, 27.0, 8.4, 16.8, 2.0, 21.0, 9.0, 30.0, 0.99, 20.0, 2.1, 8.0, 9.0, 4.5, 4.0, 1.5], "tokenOverseasOut": [203.68, 101.84, 30.55, 29.87, 339.46, 169.73, 67.89, 33.95, 61.1, 81.47, 10.18, 50.92, 10.18, 4.07, 67.89, 67.89, 40.74, 16.97, 16.97, 5.43, 2.04, 23.63, 1.9, 25.46, 8.69, 30.0, 15.0, 16.0, 30.0, 4.0, 9.6, 3.87, 19.3, 29.87, 18.0, 8.49, 101.84, 23.69, 23.15, 8.15, 16.8, 2.0, 21.0, 9.0, 30.0, 0.99, 20.0, 2.1, 8.0, 9.0, 4.5, 4.0, 1.5], "tokenDomesticOut": [203.68, 101.84, 30.55, 29.87, 339.46, 169.73, 67.89, 33.95, 61.1, 81.47, 10.18, 50.92, 10.18, 2.04, 67.89, 67.89, 40.74, 16.97, 40.74, 5.43, 2.04, 24.0, 2.0, 36.0, 8.0, 30.0, 15.0, 4.0, 30.0, 4.0, 9.6, 4.0, 28.0, 24.0, 18.0, 3.2, 100.0, 27.0, 27.0, 8.4, 16.8, 2.0, 21.0, 9.0, 30.0, 0.99, 20.0, 2.1, 8.0, 9.0, 4.5, 4.0, 1.5], "tokenThirdDiff": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.4, 0.0, -0.34, 0.0, 0.0, 0.0, 0.0, 5.09, 0.0, 0.0, 0.19, 0.05, 3.51, -0.17, 0.0, 0.0, -1.7, 0.0, 0.0, 0.0, 0.05, 1.86, -3.5, 0.0, -2.05, -0.37, 1.62, 2.02, 0.06, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "tokenOfficialDomesticDiff": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -9.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.7, 0.0, 0.0, 0.0, -0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "benchmarkLabels": ["GPT-5.6 Sol", "Kimi K3", "Claude Opus 4.8", "GPT-5.5", "Grok 4.5", "Claude Sonnet 5", "GLM-5.2", "Muse Spark 1.1", "Gemini 3.5 Flash", "Gemini 3.1 Pro Preview", "Qwen3.7-Max", "DeepSeek-V4-Pro", "Kimi K2.6", "MiniMax-M3", "MiniMax-M3 标准层 ≤512K", "MiniMax-M3 标准层 >512K", "Kimi K2.7 Code", "Hunyuan-Hy3", "Inkling", "DeepSeek-V4-Flash", "Qwen3.7-Plus", "JT-4.1 Flash", "Grok 4.3", "Mistral Medium 3.5", "Gemini 3.1 Flash-Lite", "Command A+", "ERNIE 5.1", "Mistral Small 4", "Mistral Large 3", "Llama 4 Maverick", "Llama 4 Scout", "Command R+"], "benchmarkIntel": [59, 57, 56, 55, 54, 53, 51, 51, 50, 46, 46, 44, 44, 44, 44, 44, 42, 41, 41, 40, 39, 39, 38, 30, 25, 23, 22, 20, 16, 14, 10, 8], "benchmarkCost": [4.35, 2.31, 3.85, 4.35, 1.35, 1.54, 0.9, 0.78, 1.31, 1.74, 1.43, 0.18, 0.7, 0.22, 0.22, 0.44, 0.7, 0, 1.1, 0.06, 0.27, 0, 0.64, 1.16, 0.22, 0, 0, 0.2, 0.6, 0.34, 0.22, 3.25], "benchmarkSpeed": [42, 2, 50, 68, 11, 196, 2, 1, 25, 27, 2, 2, 3, 2, 2, 2, 3, 2, 0, 1, 3, 0, 22, 2, 6, 0, 0, 1, 1, 1, 1, 2], "benchmarkElo": [1259, 1215, 1195, 1217, 1173, 1143, 1098, 1098, 1102, 1062, 1062, 1081, 1081, 1079, 1079, 1079, 1041, 1042, 1035, 1041, 1023, 0, 1035, 1000, 927, 952, 945, 962, 960, 910, 885, 900], "benchmarkCodingLabels": ["Claude Fable 5", "Gemini 3.1 Pro Preview", "Kimi K3", "Muse Spark 1.1", "GPT-5.6 Sol", "GPT-5.4", "GPT-5.4 mini", "GPT-5.5", "Grok 4.5", "Claude Sonnet 5", "Claude Opus 4.8", "Kimi K2.6", "Gemini 3.5 Flash", "GLM-5.2", "DeepSeek-V4-Pro", "Qwen3.7-Max", "Kimi K2.7 Code", "Grok 4.3", "o4 Mini", "Grok 4.20", "Qwen3.7-Plus", "MiniMax-M3", "MiniMax-M3 标准层 ≤512K", "MiniMax-M3 标准层 >512K", "DeepSeek-V4-Flash", "GLM-5.1 Pro", "Hunyuan-Hy3", "Mistral Medium 3.5", "Mistral Large 3", "Llama 4 Maverick", "Llama 4 Scout"], "benchmarkCodingAgent": [60.2, 58.9, 58.7, 58.2, 56.9, 56.6, 56.6, 56.1, 54.1, 53.6, 53.5, 53.5, 53.1, 50.5, 50.0, 48.8, 47.5, 47.3, 46.5, 45.6, 45.5, 45.4, 45.4, 45.4, 44.9, 43.8, 41.2, 39.6, 36.2, 33.1, 17.0], "profitLabels": ["寒武纪 MLU370-X8", "RTX 5090", "RTX 4090", "H100 80G", "昇腾 910C", "A100 80G", "海光 DCU K100", "摩尔线程 MTT S4000", "昇腾 910B", "壁仞 BR100"], "profitPayback": [8.6, 28.3, 29.5, 35.5, 35.5, 46.0, 64.5, 117.6, 126.7, 133.3], "profitYield": ["11.63%", "3.53%", "3.39%", "2.82%", "2.82%", "2.17%", "1.55%", "0.85%", "0.79%", "0.75%"], "profitRoiStatus": ["参考测算", "参考测算", "参考测算", "参考测算", "参考测算", "参考测算", "参考测算", "参考测算", "参考测算", "参考测算"]};
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  function init(id, option) {
    var el = document.getElementById(id);
    if (!el || !window.echarts) return;
    var c = echarts.init(el, undefined, {renderer:'svg'});
    c.setOption(option);
    window.addEventListener('resize', function(){c.resize();});
  }
  var domesticPalette = {
    '公开成交/主口径价': '#22c55e',
    '低置信观察': '#f97316',
    '云价折算': '#a78bfa',
    '价格待补': '#64748b'
  };
  function legendForKinds(kinds) {
    if (!kinds) return undefined;
    var seen = {};
    return kinds.filter(function(k){ if (seen[k]) return false; seen[k] = true; return true; });
  }
  function formatBarLabel(p, ratios) {
    if (p.value === null || p.value === undefined || p.value === '') return '';
    var rawRatio = ratios && ratios[p.dataIndex] ? ratios[p.dataIndex] : '';
    if (isMobile) {
      var short = '';
      if (rawRatio === '价格待补') short = '待补';
      else if (rawRatio === '海外缺口') short = '缺口';
      else if (rawRatio && String(rawRatio).indexOf('%') >= 0) short = rawRatio.replace('海外', '');
      else if (rawRatio) short = rawRatio.substring(0, 2);
      return short ? (p.value + '万·' + short) : (p.value + '万');
    }
    var tagMap = {'海外缺口':'缺口','云折':'云折','低置信观察':'低置信','价格待补':'待补'};
    var tag = tagMap[rawRatio] || (rawRatio && String(rawRatio).indexOf('%') >= 0 ? rawRatio : '');
    return tag ? (p.value + '\n' + tag) : String(p.value);
  }
  var isMobile = window.innerWidth <= 768;
  function bar(id, labels, values, name, color, ratios, kinds) {
    var positiveValues = values.filter(function(v){return v > 0;});
    var maxVal = positiveValues.length > 0 ? Math.max.apply(null, positiveValues) : 1;
    var yMax = maxVal > 0 ? Math.ceil((maxVal * 1.3) / 5) * 5 : undefined;
    var seriesData = values.map(function(v, i) {
      var kind = kinds && kinds[i] ? kinds[i] : '';
      var radius = isMobile ? [0,6,6,0] : [6,6,0,0];
      return {value:v, itemStyle:{color:domesticPalette[kind] || color, borderRadius:radius}};
    });
    var series = [];
    var legend = legendForKinds(kinds);
    var labelPos = isMobile ? 'right' : 'top';
    if (legend) {
      series = legend.map(function(kind) {
        return {name:kind,type:'bar',data:seriesData.map(function(d, i){return kinds[i] === kind ? d : null;}),barGap:'-100%',label:{show:true,position:labelPos,color:ink,fontSize:isMobile?11:12,formatter:function(p){return formatBarLabel(p, ratios);}},itemStyle:{borderRadius:isMobile?[0,6,6,0]:[6,6,0,0]}};
      });
    } else {
      series = [{type:'bar',data:seriesData,label:{show:true,position:labelPos,color:ink,fontSize:isMobile?11:12,formatter:function(p){
        return formatBarLabel(p, ratios);
      }},itemStyle:{borderRadius:isMobile?[0,6,6,0]:[6,6,0,0]}}];
    }
    if (isMobile) {
      init(id, {
        animation:false,
        color:legend ? legend.map(function(k){return domesticPalette[k] || color;}) : [color],
        tooltip:{trigger:'axis', appendToBody:true},
        legend:legend ? {top:0,textStyle:{color:muted}} : undefined,
        grid:{left:2,right:65,top:legend?62:36,bottom:20,containLabel:true},
        yAxis:{type:'category',data:labels,axisLabel:{color:muted,interval:0,fontSize:10,width:70,overflow:'truncate',align:'right'},axisLine:{lineStyle:{color:rule}},axisTick:{show:false},inverse:true},
        xAxis:{type:'value',name:'',max:yMax,axisLabel:{color:muted,fontSize:10},splitLine:{lineStyle:{color:rule}}},
        series:series
      });
    } else {
      init(id, {
        animation:false,
        color:legend ? legend.map(function(k){return domesticPalette[k] || color;}) : [color],
        tooltip:{trigger:'axis', appendToBody:true},
        legend:legend ? {top:0,textStyle:{color:muted}} : undefined,
        grid:{left:70,right:40,top:legend ? 80 : 52,bottom:100,containLabel:true},
        xAxis:{type:'category',data:labels,axisLabel:{color:muted,interval:0,rotate:35,fontSize:11},axisLine:{lineStyle:{color:rule}},axisTick:{show:false}},
        yAxis:{type:'value',name:name,max:yMax,nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
        series:series
      });
    }
  }
  function tokenGrouped(id, labels, series, yName) {
    var s = series.map(function(s){return {name:s.name,type:'bar',data:s.data,label:{show:false},itemStyle:{borderRadius:isMobile?[0,4,4,0]:[4,4,0,0]}};});
    if (isMobile) {
      init(id, {
        animation:false,
        color:[accent, accent2, muted],
        tooltip:{trigger:'axis', appendToBody:true},
        legend:{top:0,textStyle:{color:muted}},
        grid:{left:2,right:65,top:50,bottom:28,containLabel:true},
        yAxis:{type:'category',data:labels,axisLabel:{color:muted,interval:0,fontSize:10,width:70,overflow:'truncate',align:'right'},axisLine:{lineStyle:{color:rule}},axisTick:{show:false},inverse:true},
        xAxis:{type:'value',name:'',axisLabel:{color:muted,fontSize:10},splitLine:{lineStyle:{color:rule}}},
        series:s
      });
    } else {
      init(id, {
        animation:false,
        color:[accent, accent2, muted],
        tooltip:{trigger:'axis', appendToBody:true},
        legend:{top:0,textStyle:{color:muted}},
        grid:{left:70,right:30,top:56,bottom:120,containLabel:true},
        xAxis:{type:'category',data:labels,axisLabel:{color:muted,interval:0,rotate:35},axisLine:{lineStyle:{color:rule}},axisTick:{show:false}},
        yAxis:{type:'value',name:yName,nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
        series:s
      });
    }
  }
  function diffBar(id, labels, values, name) {
    if (isMobile) {
      init(id, {
        animation:false,
        tooltip:{trigger:'axis', appendToBody:true},
        grid:{left:2,right:65,top:40,bottom:28,containLabel:true},
        yAxis:{type:'category',data:labels,axisLabel:{color:muted,interval:0,fontSize:10,width:70,overflow:'truncate',align:'right'},axisLine:{lineStyle:{color:rule}},axisTick:{show:false},inverse:true},
        xAxis:{type:'value',name:'',axisLabel:{color:muted,fontSize:10},splitLine:{lineStyle:{color:rule}}},
        series:[{name:name,type:'bar',data:values,itemStyle:{borderRadius:[0,4,4,0],color:function(p){return p.value >= 0 ? accent : accent2;}},label:{show:true,position:'right',color:ink,fontSize:10,formatter:function(p){return p.value === undefined ? '' : p.value;}}}]
      });
    } else {
      init(id, {
        animation:false,
        tooltip:{trigger:'axis', appendToBody:true},
        grid:{left:70,right:30,top:44,bottom:120,containLabel:true},
        xAxis:{type:'category',data:labels,axisLabel:{color:muted,interval:0,rotate:35},axisLine:{lineStyle:{color:rule}},axisTick:{show:false}},
        yAxis:{type:'value',name:'元/百万Token',nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
        series:[{name:name,type:'bar',data:values,itemStyle:{borderRadius:[4,4,0,0],color:function(p){return p.value >= 0 ? accent : accent2;}},label:{show:true,position:'top',color:ink,formatter:function(p){return p.value === undefined ? '' : p.value;}}}]
      });
    }
  }
  bar('chart-domestic-main', DATA.domesticLabels, DATA.domesticValues, '万元/8卡整机/月', accent, DATA.domesticRatios, DATA.domesticKinds);
  bar('chart-overseas', DATA.overseasLabels, DATA.overseasValues, '万元/8卡整机/月', accent2);
  tokenGrouped('chart-token-input', DATA.tokenLabels, [
    {name:'官方输入价', data:DATA.tokenOfficialIn},
    {name:'海外三方输入价', data:DATA.tokenOverseasIn},
    {name:'境内三方输入价', data:DATA.tokenDomesticIn}
  ], '元/百万Token');
  tokenGrouped('chart-token-output', DATA.tokenLabels, [
    {name:'官方输出价', data:DATA.tokenOfficialOut},
    {name:'海外三方输出价', data:DATA.tokenOverseasOut},
    {name:'境内三方输出价', data:DATA.tokenDomesticOut}
  ], '元/百万Token');
  diffBar('chart-token-third-diff', DATA.tokenLabels, DATA.tokenThirdDiff, '境内三方 - 海外三方');
  diffBar('chart-token-official-domestic-diff', DATA.tokenLabels, DATA.tokenOfficialDomesticDiff, '官方 - 境内三方');
  // === 模型能力评测排行图表 ===
  // 图1: 柱状图 - Intelligence Index 综合智能排行（单系列）
  (function(){
    if (!DATA.benchmarkLabels || !DATA.benchmarkLabels.length) return;
    var bLabels = DATA.benchmarkLabels;
    var bIntel = DATA.benchmarkIntel;
    var bIntelMax = Math.max.apply(null, bIntel) || 1;
    if (isMobile) {
      init('chart-benchmark-intel', {
        animation:false,
        color:[accent],
        tooltip:{trigger:'axis', appendToBody:true},
        grid:{left:2,right:45,top:20,bottom:20,containLabel:true},
        yAxis:{type:'category',data:bLabels,axisLabel:{color:muted,interval:0,fontSize:9,width:65,overflow:'truncate',align:'right'},axisLine:{lineStyle:{color:rule}},axisTick:{show:false},inverse:true},
        xAxis:{type:'value',name:'',max:Math.ceil(bIntelMax*1.15),axisLabel:{color:muted,fontSize:9},splitLine:{lineStyle:{color:rule}}},
        series:[
          {name:'Intelligence Index',type:'bar',data:bIntel,label:{show:true,position:'right',color:ink,fontSize:9},itemStyle:{borderRadius:[0,4,4,0]}}
        ]
      });
    } else {
      init('chart-benchmark-intel', {
        animation:false,
        color:[accent],
        tooltip:{trigger:'axis', appendToBody:true},
        grid:{left:70,right:30,top:30,bottom:80,containLabel:true},
        xAxis:{type:'category',data:bLabels,axisLabel:{color:muted,interval:0,rotate:35,fontSize:11},axisLine:{lineStyle:{color:rule}},axisTick:{show:false}},
        yAxis:{type:'value',name:'分数',max:Math.ceil(bIntelMax*1.15),nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
        series:[
          {name:'Intelligence Index',type:'bar',data:bIntel,label:{show:true,position:'top',color:ink,fontSize:11},itemStyle:{borderRadius:[4,4,0,0]}}
        ]
      });
    }
  })();
  // 图2: 柱状图 - SciCode 编程能力排行（仅已评测模型（AA SciCode，模型级编程 pass@1%））
  (function(){
    if (!DATA.benchmarkCodingLabels || !DATA.benchmarkCodingLabels.length) return;
    var cLabels = DATA.benchmarkCodingLabels;
    var cAgent = DATA.benchmarkCodingAgent;
    var cMax = Math.max.apply(null, cAgent) || 1;
    if (isMobile) {
      init('chart-benchmark-coding', {
        animation:false,
        color:[accent2],
        tooltip:{trigger:'axis', appendToBody:true, formatter:function(p){return p[0].name + ': ' + p[0].value + '%';}},
        grid:{left:2,right:45,top:20,bottom:20,containLabel:true},
        yAxis:{type:'category',data:cLabels,axisLabel:{color:muted,interval:0,fontSize:9,width:65,overflow:'truncate',align:'right'},axisLine:{lineStyle:{color:rule}},axisTick:{show:false},inverse:true},
        xAxis:{type:'value',name:'%',max:Math.ceil(cMax*1.15),axisLabel:{color:muted,fontSize:9},splitLine:{lineStyle:{color:rule}}},
        series:[
          {name:'SciCode 编程能力',type:'bar',data:cAgent,label:{show:true,position:'right',color:ink,fontSize:9,formatter:function(p){return p.value + '%';}},itemStyle:{borderRadius:[0,4,4,0]}}
        ]
      });
    } else {
      init('chart-benchmark-coding', {
        animation:false,
        color:[accent2],
        tooltip:{trigger:'axis', appendToBody:true, formatter:function(p){return p[0].name + ': ' + p[0].value + '%';}},
        grid:{left:70,right:30,top:30,bottom:40,containLabel:true},
        xAxis:{type:'category',data:cLabels,axisLabel:{color:muted,interval:0,rotate:25,fontSize:11},axisLine:{lineStyle:{color:rule}},axisTick:{show:false}},
        yAxis:{type:'value',name:'pass@1 %',max:Math.ceil(cMax*1.15),nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
        series:[
          {name:'SciCode 编程能力',type:'bar',data:cAgent,label:{show:true,position:'top',color:ink,fontSize:11,formatter:function(p){return p.value + '%';}},itemStyle:{borderRadius:[4,4,0,0]}}
        ]
      });
    }
  })();
  // 图3: 散点图 - Cost per Task vs Intelligence（性价比概览，价格已换算为人民币）
  (function(){
    if (!DATA.benchmarkLabels || !DATA.benchmarkLabels.length) return;
    var USD2CNY = 6.7775; // 动态获取汇率（Frankfurter / ECB，日期：2026-07-19）
    var scatterData = [];
    for (var i = 0; i < DATA.benchmarkLabels.length; i++) {
      var cost = DATA.benchmarkCost[i];
      var intel = DATA.benchmarkIntel[i];
      if (cost > 0 && intel > 0) {
        scatterData.push({
          value:[cost * USD2CNY, intel],
          name:DATA.benchmarkLabels[i],
          symbolSize: 12
        });
      }
    }
    if (!scatterData.length) return;
    var xVals = scatterData.map(function(d){return d.value[0];});
    var yVals = scatterData.map(function(d){return d.value[1];});
    var xMax = Math.ceil(Math.max.apply(null, xVals) * 1.2) || 36;
    var yMax = Math.ceil(Math.max.apply(null, yVals) * 1.15) || 60;
    if (isMobile) {
      init('chart-benchmark-cost', {
        animation:false,
        tooltip:{trigger:'item', appendToBody:true, formatter:function(p){return p.name + '<br/>费用: ¥' + p.value[0].toFixed(1) + '/Task<br/>Intelligence: ' + p.value[1];}},
        grid:{left:2,right:30,top:20,bottom:20,containLabel:true},
        xAxis:{type:'value',name:'¥/Task',max:xMax,nameTextStyle:{color:muted},axisLabel:{color:muted,fontSize:9},splitLine:{lineStyle:{color:rule}}},
        yAxis:{type:'value',name:'Intel',max:yMax,axisLabel:{color:muted,fontSize:9},splitLine:{lineStyle:{color:rule}}},
        series:[{type:'scatter',data:scatterData,itemStyle:{color:accent,borderRadius:4,opacity:0.8},label:{show:false}}]
      });
    } else {
      init('chart-benchmark-cost', {
        animation:false,
        tooltip:{trigger:'item', appendToBody:true, formatter:function(p){return p.name + '<br/>费用: ¥' + p.value[0].toFixed(1) + '/Task<br/>Intelligence: ' + p.value[1];}},
        grid:{left:50,right:30,top:36,bottom:50,containLabel:true},
        xAxis:{type:'value',name:'费用/Task（¥，汇率' + USD2CNY.toFixed(2) + '）',max:xMax,nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
        yAxis:{type:'value',name:'Intelligence Index',max:yMax,nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
        series:[{type:'scatter',data:scatterData,itemStyle:{color:accent2,borderRadius:6,opacity:0.85,borderColor:accent,borderWidth:1},label:{show:true,position:'top',color:ink,fontSize:10,formatter:function(p){return p.name;}}}]
      });
    }
  })();
  // 图4: 柱状图 - 毛回本参考（按回本周期从短到长排序）
  (function(){
    if (!DATA.profitLabels || !DATA.profitLabels.length) return;
    var pLabels = DATA.profitLabels;
    var pPayback = DATA.profitPayback;
    var pYield = (DATA.profitYield || []).map(function(v){ return parseFloat(v) || 0; });
    var pMax = Math.max.apply(null, pPayback) || 1;
    var yMax = Math.max.apply(null, pYield) || 1;
    if (isMobile) {
      init('chart-profit-payback', {
        animation:false,
        color:[accent, accent2],
        tooltip:{trigger:'axis', appendToBody:true, formatter:function(p){var s=p[0].name;for(var i=0;i<p.length;i++){s+='<br/>'+p[i].seriesName+': '+p[i].value+(i===0?' 月':'%');}return s;}},
        legend:{data:['毛回本（月）','月租收益率（%）'],textStyle:{color:muted,fontSize:9},top:0,itemWidth:12,itemHeight:8},
        grid:{left:2,right:55,top:25,bottom:20,containLabel:true},
        yAxis:{type:'category',data:pLabels,axisLabel:{color:muted,interval:0,fontSize:9,width:55,overflow:'truncate',align:'right'},axisLine:{lineStyle:{color:rule}},axisTick:{show:false},inverse:true},
        xAxis:{type:'value',name:'月',max:Math.ceil(pMax*1.15),axisLabel:{color:muted,fontSize:9},splitLine:{lineStyle:{color:rule}}},
        series:[
          {name:'毛回本（月）',type:'bar',data:pPayback,label:{show:true,position:'right',color:ink,fontSize:9},itemStyle:{borderRadius:[0,4,4,0]}},
          {name:'月租收益率（%）',type:'bar',data:pYield,xAxisIndex:0,label:{show:false},itemStyle:{borderRadius:[0,4,4,0],opacity:0.6}}
        ]
      });
    } else {
      init('chart-profit-payback', {
        animation:false,
        color:[accent, accent2],
        tooltip:{trigger:'axis', appendToBody:true, formatter:function(p){var s=p[0].name;for(var i=0;i<p.length;i++){s+='<br/>'+p[i].seriesName+': '+p[i].value+(i===0?' 月':'%');}return s;}},
        legend:{data:['毛回本（月）','月租收益率（%）'],textStyle:{color:muted},top:0,itemWidth:14,itemHeight:10},
        grid:{left:70,right:50,top:40,bottom:50,containLabel:true},
        xAxis:{type:'category',data:pLabels,axisLabel:{color:muted,interval:0,rotate:25,fontSize:11},axisLine:{lineStyle:{color:rule}},axisTick:{show:false}},
        yAxis:{type:'value',name:'月',max:Math.ceil(pMax*1.15),nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
        series:[
          {name:'毛回本（月）',type:'bar',data:pPayback,label:{show:true,position:'top',color:ink,fontSize:11},itemStyle:{borderRadius:[4,4,0,0]}},
          {name:'月租收益率（%）',type:'bar',data:pYield,xAxisIndex:0,label:{show:true,position:'top',color:muted,fontSize:9},itemStyle:{borderRadius:[4,4,0,0],opacity:0.6}}
        ]
      });
    }
  })();
})();