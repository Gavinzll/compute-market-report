(function(){
  var DATA = {"domesticLabels": ["H100 80G", "H20", "A100 80G", "RTX 5090", "RTX 4090", "昇腾 910C"], "domesticValues": [7.6, 4.8, 3.15, 1.2, 0.73, 6.2], "domesticRatios": ["61.4%", "海外缺口", "51.1%", "29.3%", "25.6%", "海外缺口"], "overseasLabels": ["B300", "B200", "H200", "H100 80G", "A100 80G", "L40S", "L4", "RTX 5090", "RTX 4090"], "overseasValues": [30.56, 27.67, 18.16, 12.37, 6.16, 4.1, 1.61, 4.1, 2.85]};
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
  bar('chart-domestic-main', DATA.domesticLabels, DATA.domesticValues, '万元/8卡整机/月', accent, DATA.domesticRatios);
  bar('chart-overseas', DATA.overseasLabels, DATA.overseasValues, '万元/8卡整机/月', accent2);
})();