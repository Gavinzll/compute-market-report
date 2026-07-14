(function(){
  var DATA = {"domesticLabels": ["H100 80G", "RTX 5090"], "domesticValues": [7.6, 1.2], "overseasLabels": ["B300", "B200", "H200", "H100 80G", "A100 80G", "L40S", "L4", "RTX 5090", "RTX 4090"], "overseasValues": [53.06, 48.03, 31.52, 21.47, 10.7, 7.11, 2.8, 7.11, 4.95]};
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  function init(id, option) {
    var el = document.getElementById(id);
    if (!el || !window.echarts) return;
    var c = echarts.init(el, null, {renderer:'svg'});
    c.setOption(option);
    window.addEventListener('resize', function(){c.resize();});
  }
  function bar(id, labels, values, name, color) {
    init(id, {
      animation:false,
      color:[color],
      tooltip:{trigger:'axis', appendToBody:true},
      grid:{left:70,right:40,top:44,bottom:80,containLabel:true},
      xAxis:{type:'category',data:labels,axisLabel:{color:muted,interval:0},axisLine:{lineStyle:{color:rule}},axisTick:{show:false}},
      yAxis:{type:'value',name:name,nameTextStyle:{color:muted},axisLabel:{color:muted},splitLine:{lineStyle:{color:rule}}},
      series:[{type:'bar',data:values,label:{show:true,position:'top',color:ink},itemStyle:{borderRadius:[6,6,0,0]}}]
    });
  }
  bar('chart-domestic-main', DATA.domesticLabels, DATA.domesticValues, '万元/8卡整机/月', accent);
  bar('chart-overseas', DATA.overseasLabels, DATA.overseasValues, '人民币/卡/小时', accent2);
})();