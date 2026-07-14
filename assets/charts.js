(function() {
  var DATA = {"tokenLabels": ["火山引擎\\nDoubao 低价入口", "阿里云/通义千问\\nqwen-flash-character", "阿里云/通义千问\\nqwen-plus-character", "DeepSeek\\ndeepseek-v4-flash", "阿里云/通义千问\\nqwen-max", "DeepSeek\\ndeepseek-v4-pro", "百度\\nERNIE 3.5", "OpenAI\\nGPT-5.4 mini", "火山引擎\\nDoubao 文本模型", "Google\\nGemini 2.5 Pro", "OpenAI\\nGPT-5.4", "Anthropic\\nClaude Sonnet 4.6", "百度\\nERNIE 4.0", "OpenAI\\nGPT-5.5", "Anthropic\\nClaude Opus 4.6"], "tokenRegion": ["国产", "国产", "国产", "国产", "国产", "国产", "国产", "海外", "国产", "海外", "海外", "海外", "国产", "海外", "海外"], "tokenInput": [0.15, 0.25, 0.8, 1.0, 2.4, 3.0, 4.0, 5.38, 6.0, 8.97, 17.95, 21.54, 30.0, 35.9, 35.9], "tokenOutput": [null, 1.5, 2.0, 2.0, 9.6, 6.0, 8.0, 32.31, 80.0, 71.8, 107.7, 107.7, 90.0, 215.4, 179.5], "domesticLabels": ["B200\\n8卡月租≈27.65万元/月\\n国内/海外=100.0%", "H200\\n8卡月租≈19.01万元/月\\n国内/海外=108.0%", "H100 80G\\n8卡月租≈60.83万元/月\\n国内/海外=591.0%", "H800\\n8卡月租≈33.41万元/月\\n国内/海外=缺口径", "H20\\n8卡月租≈14.98万元/月\\n国内/海外=缺口径", "A100 80G\\n8卡月租≈10.43万元/月\\n国内/海外=195.0%", "A800\\n8卡月租≈4.03万元/月\\n国内/海外=缺口径", "L40S\\n8卡月租≈3.57万元/月\\n国内/海外=102.0%", "L20\\n8卡月租≈2.48万元/月\\n国内/海外=缺口径", "L4\\n8卡月租≈0.63万元/月\\n国内/海外=61.0%", "RTX 5090\\n8卡月租≈1.2万元/月\\n国内/海外=45.0%", "RTX 4090\\n8卡月租≈0.95万元/月\\n国内/海外=66.0%", "昇腾 910B\\n8卡月租≈12.67万元/月\\n国内/海外=缺口径"], "domesticValues": [48.0, 33.0, 105.6, 58.0, 26.0, 18.1, 7.0, 6.2, 4.3, 1.1, 2.08, 1.65, 22.0], "overseasLabels": ["B200\\n8卡月租≈27.67万元/月", "H200\\n8卡月租≈17.66万元/月", "H100 80G\\n8卡月租≈10.3万元/月", "A100 80G\\n8卡月租≈5.33万元/月", "L40S\\n8卡月租≈3.51万元/月", "L4\\n8卡月租≈1.03万元/月", "RTX 5090\\n8卡月租≈2.69万元/月", "RTX 4090\\n8卡月租≈1.45万元/月"], "overseasValues": [48.03, 30.66, 17.88, 9.26, 6.1, 1.79, 4.67, 2.51], "procLabels": ["B200", "H200", "H100 80G", "H800", "H20", "A100 80G", "A800", "L40S", "RTX 5090", "RTX 4090", "L20", "L4", "昇腾 910B"], "procValues": [390000, 280000, 235000, 180000, 105000, 87500, 62500, 57500, 24000, 17000, 25000, 17500, 95000], "paybackLabels": ["B200", "H200", "H100 80G", "H800", "H20", "A100 80G", "A800", "L40S", "RTX 5090", "RTX 4090", "L20", "L4", "昇腾 910B"], "paybackValues": [13.3, 13.9, 3.6, 5.1, 6.6, 7.9, 14.6, 15.2, 18.9, 16.8, 9.5, 26.0, 7.1], "date": "2026-07-14"};
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
    var c = echarts.init(el, null, { renderer: 'svg' });
    c.setOption(option);
    window.addEventListener('resize', function() { c.resize(); });
  }
    function grid() { return { left: 72, right: 40, top: 56, bottom: 150, containLabel:true }; }
  function axis() { return { axisLine: { lineStyle: { color: rule } }, axisTick: { show:false }, axisLabel: { color: muted }, splitLine: { lineStyle: { color: rule } } }; }
  function bar(id, labels, values, name, color) {
    init(id, {
      animation:false, color:[color], tooltip:{ trigger:'axis', appendToBody:true },
      grid:grid(), xAxis:Object.assign({ type:'category', data:labels, axisLabel:{ color:muted, rotate:35, interval:0 } }, { axisLine:{lineStyle:{color:rule}}, axisTick:{show:false} }),
      yAxis:Object.assign({ type:'value', name:name, nameTextStyle:{ color:muted } }, axis()),
      series:[{ type:'bar', data:values, label:{ show:true, position:'top', color:ink, fontSize:10 }, itemStyle:{ borderRadius:[6,6,0,0] } }]
    });
  }
  function hbar(id, labels, values, name, color) {
    init(id, {
      animation:false, color:[color], tooltip:{ trigger:'axis', appendToBody:true },
      grid:{ left:210, right:92, top:38, bottom:44, containLabel:false },
      xAxis:Object.assign({ type:'value', name:name, nameTextStyle:{ color:muted } }, axis()),
      yAxis:{ type:'category', data:labels.reverse(), axisLabel:{ color:muted, fontSize:10, lineHeight:14, width:190, overflow:'break' }, axisLine:{lineStyle:{color:rule}}, axisTick:{show:false} },
      series:[{ type:'bar', data:values.reverse(), label:{ show:true, position:'right', color:ink, fontSize:10, formatter:function(p){ return p.value + ' 元'; } }, itemStyle:{ borderRadius:[0,6,6,0] } }]
    });
  }
  bar('chart-token-input', DATA.tokenLabels, DATA.tokenInput, '人民币/百万Token（输入）', accent);
  bar('chart-token-output', DATA.tokenLabels, DATA.tokenOutput, '人民币/百万Token（输出）', accent2);
  hbar('chart-domestic-rental', DATA.domesticLabels.slice(), DATA.domesticValues.slice(), '人民币/卡/小时', accent);
  hbar('chart-overseas-rental', DATA.overseasLabels.slice(), DATA.overseasValues.slice(), '人民币/卡/小时', accent2);
  bar('chart-procurement', DATA.procLabels, DATA.procValues, '人民币/单卡', accent);
  bar('chart-payback', DATA.paybackLabels, DATA.paybackValues, '月', accent2);
  init('chart-rental-trend', { animation:false, tooltip:{trigger:'axis', appendToBody:true}, legend:{textStyle:{color:muted}}, grid:grid(), xAxis:{type:'category', data:[DATA.date], axisLabel:{color:muted}, axisLine:{lineStyle:{color:rule}}}, yAxis:Object.assign({type:'value', name:'人民币/卡/小时'}, axis()), series:[{name:'H100 80G', type:'line', data:[105.6], color:accent}, {name:'H200', type:'line', data:[33], color:accent2}, {name:'RTX 5090', type:'line', data:[2.08], color:muted}] });
  init('chart-token-trend', { animation:false, tooltip:{trigger:'axis', appendToBody:true}, legend:{textStyle:{color:muted}}, grid:grid(), xAxis:{type:'category', data:[DATA.date], axisLabel:{color:muted}, axisLine:{lineStyle:{color:rule}}}, yAxis:Object.assign({type:'value', name:'人民币/百万Token'}, axis()), series:[{name:'DeepSeek V4 Flash 输入', type:'line', data:[1], color:accent}, {name:'Qwen3-Max 输入', type:'line', data:[2.5], color:accent2}, {name:'OpenAI GPT-5.4 mini 输入', type:'line', data:[5.39], color:muted}] });
})();
