(function(){
  var DATA = {"domesticLabels": ["B300", "B200", "H200", "H100 80G", "H800", "A100 80G", "L40S", "L20", "L4", "RTX 5090", "RTX 4090", "昇腾 910C", "昇腾 910B", "昇腾 950PR", "寒武纪 MLU370-X8", "寒武纪 MLU590", "海光 DCU K100", "海光 DCU Z100", "壁仞 BR100", "摩尔线程 MTT S4000", "摩尔线程 MTT S5000"], "domesticValues": [28.0, 13.0, 9.4, 7.75, 6.9, 2.5, 1.2, 6.04, 4.64, 1.2, 0.78, 6.2, 1.5, 0, 4.99, 0, 4.0, 0, 4.3, 3.5, 0], "domesticRatios": ["91.6%", "47.0%", "51.8%", "62.7%", "海外缺口", "40.6%", "29.3%", "海外缺口", "288.2%", "29.3%", "27.4%", "海外缺口", "海外缺口", "价格待补", "云价折算", "价格待补", "市场核价", "价格待补", "市场核价", "市场核价", "价格待补"], "domesticKinds": ["公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "云价折算", "云价折算", "公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "公开成交/主口径价", "价格待补", "云价折算", "价格待补", "市场核价", "价格待补", "市场核价", "市场核价", "价格待补"], "overseasLabels": ["GB300", "GB200", "B300", "B200", "H200", "H100 80G", "A100 80G", "L40S", "L4", "RTX 5090", "RTX 4090"], "overseasValues": [55.05, 54.79, 35.94, 25.56, 17.37, 13.28, 8.85, 5.37, 2.65, 3.1, 2.44], "tokenLabels": ["OpenAI\\nGPT-5.5", "OpenAI\\nGPT-5.4", "OpenAI\\nGPT-5.4 mini", "OpenAI\\no4 Mini", "Anthropic\\nClaude Fable 5", "Anthropic\\nClaude Opus 4.8", "Anthropic\\nClaude Sonnet 5", "Anthropic\\nClaude Haiku 4.5", "Google\\nGemini 3.5 Flash", "Google\\nGemini 3.1 Pro Preview", "Google\\nGemini 3.1 Flash-Lite", "Mistral\\nMistral Medium 3.5", "Mistral\\nMistral Large 3", "Mistral\\nMistral Small 4", "Cohere\\nCommand A+", "Cohere\\nCommand R+", "xAI Grok\\nGrok 4.5", "xAI Grok\\nGrok 4.3", "xAI Grok\\nGrok 4.20", "Meta Llama\\nLlama 4 Maverick", "Meta Llama\\nLlama 4 Scout", "DeepSeek\\nDeepSeek-V4-Pro", "DeepSeek\\nDeepSeek-V4-Flash", "阿里云/通义千问\\nQwen3.7-Max", "阿里云/通义千问\\nQwen3.7-Plus", "火山方舟/豆包\\nDoubao-Seed 2.1 Pro", "火山方舟/豆包\\nDoubao-Seed 2.1 Turbo", "火山方舟/豆包\\nDoubao-Seed 2.0 Pro", "火山方舟/豆包\\nDoubao-Seed-Evolving", "腾讯混元\\nHunyuan-Hy3", "腾讯混元\\nHunyuan-role-latest", "腾讯混元\\nHunyuan-A13B", "智谱 GLM / Z.ai\\nGLM-5.2", "智谱 GLM / Z.ai\\nGLM-5.1 Pro", "百度文心\\nERNIE 5.1", "百度文心\\nERNIE-4.5-Turbo", "Kimi / Moonshot\\nKimi K2.7 Code", "Kimi / Moonshot\\nKimi K2.6", "MiniMax\\nMiniMax-M3 标准层 ≤512K", "MiniMax\\nMiniMax-M3 标准层 >512K", "讯飞星火\\nSpark X2", "讯飞星火\\nSpark Max", "百川智能\\nBaichuan-M3-Plus", "百川智能\\nBaichuan-M3", "零一万物\\nYi-Lightning", "零一万物\\nYi-Large", "阶跃星辰\\nStep 3.5 Flash", "阶跃星辰\\nStep-R1-V-Mini", "商汤日日新\\nSenseNova-V6.5-Pro", "商汤日日新\\nSenseNova-V6.5-Turbo", "昆仑万维天工\\nSkyClaw-v1.0", "昆仑万维天工\\nSkyClaw-v1.0-lite"], "tokenOfficialIn": [35.9, 17.95, 5.38, 7.9, 71.8, 35.9, 14.36, 7.18, 10.77, 14.36, 1.79, 14.36, 3.59, 0.72, 17.95, 17.95, 14.36, 8.97, 14.36, 1.44, 0.72, 3.0, 1.0, 12.0, 2.0, 6.0, 3.0, 3.2, 6.0, 1.0, 2.4, 0.5, 8.0, 6.0, 4.0, 0.8, 6.5, 6.5, 2.1, 4.2, 1.0, 21.0, 5.0, 10.0, 0.99, 20.0, 0.7, 2.5, 3.0, 1.5, 0.5, 0.3], "tokenOverseasIn": [35.9, 17.95, 5.38, 7.9, 71.8, 35.9, 14.36, 7.18, 10.77, 14.36, 1.79, 10.77, 3.59, 1.08, 17.95, 17.95, 14.36, 8.97, 8.97, 1.44, 0.72, 12.49, 1.01, 8.97, 2.3, 6.0, 3.0, 3.2, 6.0, 1.0, 2.4, 1.01, 6.49, 10.05, 4.0, 3.02, 5.16, 4.74, 2.15, 4.2, 1.0, 21.0, 5.0, 10.0, 0.99, 20.0, 0.7, 2.5, 3.0, 1.5, 0.5, 0.3], "tokenDomesticIn": [35.9, 17.95, 5.38, 7.9, 71.8, 35.9, 14.36, 7.18, 10.77, 14.36, 1.79, 14.36, 3.59, 0.72, 17.95, 17.95, 14.36, 8.97, 14.36, 1.44, 0.72, 12.0, 1.0, 12.0, 2.0, 6.0, 3.0, 1.5, 6.0, 1.0, 2.4, 1.0, 8.0, 6.0, 4.0, 0.8, 6.5, 6.5, 2.1, 4.2, 1.0, 21.0, 5.0, 10.0, 0.99, 20.0, 0.7, 2.5, 3.0, 1.5, 0.5, 0.3], "tokenOfficialOut": [215.4, 107.7, 32.31, 31.59, 359.0, 179.5, 71.8, 35.9, 64.62, 86.16, 10.77, 53.85, 10.77, 2.15, 71.8, 71.8, 43.08, 17.95, 43.08, 5.74, 2.15, 6.0, 2.0, 36.0, 8.0, 30.0, 15.0, 16.0, 30.0, 4.0, 9.6, 2.0, 28.0, 24.0, 18.0, 3.2, 27.0, 27.0, 8.4, 16.8, 2.0, 21.0, 9.0, 30.0, 0.99, 20.0, 2.1, 8.0, 9.0, 4.5, 4.0, 1.5], "tokenOverseasOut": [215.4, 107.7, 32.31, 31.59, 359.0, 179.5, 71.8, 35.9, 64.62, 86.16, 10.77, 53.85, 10.77, 4.31, 71.8, 71.8, 43.08, 17.95, 17.95, 5.74, 2.15, 24.99, 2.01, 26.92, 9.19, 30.0, 15.0, 16.0, 30.0, 4.0, 9.6, 4.09, 20.41, 31.59, 18.0, 8.97, 25.06, 24.48, 8.62, 16.8, 2.0, 21.0, 9.0, 30.0, 0.99, 20.0, 2.1, 8.0, 9.0, 4.5, 4.0, 1.5], "tokenDomesticOut": [215.4, 107.7, 32.31, 31.59, 359.0, 179.5, 71.8, 35.9, 64.62, 86.16, 10.77, 53.85, 10.77, 2.15, 71.8, 71.8, 43.08, 17.95, 43.08, 5.74, 2.15, 24.0, 2.0, 36.0, 8.0, 30.0, 15.0, 4.0, 30.0, 4.0, 9.6, 4.0, 28.0, 24.0, 18.0, 3.2, 27.0, 27.0, 8.4, 16.8, 2.0, 21.0, 9.0, 30.0, 0.99, 20.0, 2.1, 8.0, 9.0, 4.5, 4.0, 1.5], "tokenThirdDiff": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.59, 0.0, -0.36, 0.0, 0.0, 0.0, 0.0, 5.39, 0.0, 0.0, -0.49, -0.01, 3.03, -0.3, 0.0, 0.0, -1.7, 0.0, 0.0, 0.0, -0.01, 1.51, -4.05, 0.0, -2.22, 1.34, 1.76, -0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], "tokenOfficialDomesticDiff": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -9.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.7, 0.0, 0.0, 0.0, -0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]};
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
    '云价折算': '#8b5cf6',
    '市场核价': '#38bdf8',
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
    var tagMap = {'海外缺口':'缺口','云价折算':'云折','市场核价':'市核','价格待补':'待补'};
    var tag = tagMap[rawRatio] || (rawRatio && String(rawRatio).indexOf('%') >= 0 ? rawRatio : '');
    return tag ? (p.value + '\n' + tag) : String(p.value);
  }
  var isMobile = window.innerWidth <= 768;
  function bar(id, labels, values, name, color, ratios, kinds) {
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
        xAxis:{type:'value',name:'',axisLabel:{color:muted,fontSize:10},splitLine:{lineStyle:{color:rule}}},
        series:series
      });
    } else {
      init(id, {
        animation:false,
        color:legend ? legend.map(function(k){return domesticPalette[k] || color;}) : [color],
        tooltip:{trigger:'axis', appendToBody:true},
        legend:legend ? {top:0,textStyle:{color:muted}} : undefined,
        grid:{left:70,right:40,top:legend ? 72 : 44,bottom:100,containLabel:true},
        xAxis:{type:'category',data:labels,axisLabel:{color:muted,interval:0,rotate:35,fontSize:11},axisLine:{lineStyle:{color:rule}},axisTick:{show:false}},
        yAxis:{type:'value',name:name,nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
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
})();