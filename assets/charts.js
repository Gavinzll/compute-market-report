(function(){
  var DATA = {"domesticLabels": ["H100 80G", "H20", "A100 80G", "RTX 5090", "RTX 4090", "昇腾 910C"], "domesticValues": [7.6, 4.8, 3.15, 1.2, 0.73, 6.2], "domesticRatios": ["61.4%", "海外缺口", "51.1%", "29.3%", "25.6%", "海外缺口"], "overseasLabels": ["B300", "B200", "H200", "H100 80G", "A100 80G", "L40S", "L4", "RTX 5090", "RTX 4090"], "overseasValues": [30.56, 27.67, 18.16, 12.37, 6.16, 4.1, 1.61, 4.1, 2.85], "tokenLabels": ["OpenAI\\ngpt-5", "OpenAI\\ngpt-5-mini", "Anthropic\\nclaude-sonnet-5", "Anthropic\\nclaude-haiku-5", "Google\\ngemini-2.5-pro", "Google\\ngemini-2.5-flash", "DeepSeek\\nDeepSeek-V4-Flash", "DeepSeek\\nDeepSeek-V4-Pro", "阿里云/通义千问\\nqwen3.7-max", "阿里云/通义千问\\nqwen3.7-plus", "火山方舟/豆包\\ndoubao-seed-1.6", "火山方舟/豆包\\nSeed-OSS-36B", "腾讯混元\\nHunyuan-A13B", "腾讯混元\\nHunyuan-role-latest", "Kimi / Moonshot\\nKimi-K2.7-Code", "Kimi / Moonshot\\nKimi-K2.6", "智谱 GLM / Z.ai\\nGLM-5.2", "百度文心\\nERNIE-4.5-Turbo-VL-32K", "百度文心\\nERNIE 5.0 0-32K", "百度文心\\nERNIE 5.0 32K-128K", "MiniMax\\nMiniMax-M3 标准层 ≤512K", "MiniMax\\nMiniMax-M3 标准层 >512K", "MiniMax\\nMiniMax-M3 优先服务 ≤512K"], "tokenOfficialIn": [8.97, 1.79, 14.36, null, 8.97, 2.15, 1.0, 3.0, 12.0, 2.0, 0.8, null, 0.5, 2.4, 6.5, 6.5, 8.0, 3.0, 6.0, 10.0, 2.1, 4.2, 3.15], "tokenOverseasIn": [8.97, 1.79, 14.36, 5.74, 8.97, 2.15, 0.65, 3.12, 8.97, 2.3, null, null, 1.01, null, 5.16, 4.74, 6.68, 3.02, null, null, 2.15, null, null], "tokenDomesticIn": [null, null, null, null, null, null, 1.0, 12.0, null, null, null, 1.5, 1.0, null, 6.5, 6.5, 8.0, null, null, null, 2.1, null, null], "tokenOfficialOut": [71.8, 14.36, 71.8, null, 71.8, 17.95, 2.0, 6.0, 36.0, 8.0, 2.0, null, 2.0, 9.6, 27.0, 27.0, 28.0, 9.0, 24.0, 40.0, 8.4, 16.8, 12.6], "tokenOverseasOut": [71.8, 14.36, 71.8, 28.72, 71.8, 17.95, 1.29, 6.25, 26.92, 9.19, null, null, 4.09, null, 25.06, 24.48, 21.54, 8.97, null, null, 8.62, null, null], "tokenDomesticOut": [null, null, null, null, null, null, 2.0, 24.0, null, null, null, 4.0, 4.0, null, 27.0, 27.0, 28.0, null, null, null, 8.4, null, null], "tokenThirdDiff": [null, null, null, null, null, null, 0.35, 8.88, null, null, null, null, -0.01, null, 1.34, 1.76, 1.32, null, null, null, -0.05, null, null], "tokenOfficialDomesticDiff": [null, null, null, null, null, null, 0.0, -9.0, null, null, null, null, -0.5, null, 0.0, 0.0, 0.0, null, null, null, 0.0, null, null]};
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
    var c = echarts.init(el, null, {renderer:'svg'});
    c.setOption(option);
    window.addEventListener('resize', function(){c.resize();});
  }
  function bar(id, labels, values, name, color, ratios) {
    init(id, {
      animation:false,
      color:[color],
      tooltip:{trigger:'axis', appendToBody:true},
      grid:{left:70,right:40,top:44,bottom:80,containLabel:true},
      xAxis:{type:'category',data:labels,axisLabel:{color:muted,interval:0},axisLine:{lineStyle:{color:rule}},axisTick:{show:false}},
      yAxis:{type:'value',name:name,nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
      series:[{type:'bar',data:values,label:{show:true,position:'top',color:ink,formatter:function(p){
        var base = p.value + '万/月';
        var rawRatio = ratios && ratios[p.dataIndex] ? ratios[p.dataIndex] : '';
        var ratio = rawRatio === '海外缺口' ? ' · 海外缺口' : (rawRatio ? ' · 海外' + rawRatio : '');
        return base + ratio;
      }},itemStyle:{borderRadius:[6,6,0,0]}}]
    });
  }
  function tokenGrouped(id, labels, series, yName) {
    init(id, {
      animation:false,
      color:[accent, accent2, muted],
      tooltip:{trigger:'axis', appendToBody:true},
      legend:{top:0,textStyle:{color:muted}},
      grid:{left:70,right:30,top:56,bottom:120,containLabel:true},
      xAxis:{type:'category',data:labels,axisLabel:{color:muted,interval:0,rotate:35},axisLine:{lineStyle:{color:rule}},axisTick:{show:false}},
      yAxis:{type:'value',name:yName,nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
      series:series.map(function(s){return {name:s.name,type:'bar',data:s.data,label:{show:false},itemStyle:{borderRadius:[4,4,0,0]}};})
    });
  }
  function diffBar(id, labels, values, name) {
    init(id, {
      animation:false,
      tooltip:{trigger:'axis', appendToBody:true},
      grid:{left:70,right:30,top:44,bottom:120,containLabel:true},
      xAxis:{type:'category',data:labels,axisLabel:{color:muted,interval:0,rotate:35},axisLine:{lineStyle:{color:rule}},axisTick:{show:false}},
      yAxis:{type:'value',name:'元/百万Token',nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
      series:[{name:name,type:'bar',data:values,itemStyle:{borderRadius:[4,4,0,0],color:function(p){return p.value >= 0 ? accent : accent2;}},label:{show:true,position:'top',color:ink,formatter:function(p){return p.value == null ? 'N/A' : p.value;}}}]
    });
  }
  bar('chart-domestic-main', DATA.domesticLabels, DATA.domesticValues, '万元/8卡整机/月', accent, DATA.domesticRatios);
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