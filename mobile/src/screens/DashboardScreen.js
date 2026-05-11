import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, RefreshControl, Dimensions, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LineChart } from 'react-native-chart-kit';
import Svg, { Circle } from 'react-native-svg';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import api from '../services/api';

const W = Dimensions.get('window').width;

function DonutChart({ data, size, strokeWidth, theme }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;
  const total = data.reduce((sum, d) => sum + d.value, 0) || 1;

  let accumulated = 0;
  const segments = data.map(d => {
    const pct = d.value / total;
    const offset = circumference * (1 - pct);
    const rotation = accumulated * 360 - 90;
    accumulated += pct;
    return { ...d, offset, rotation, pct };
  });

  return (
    <View style={{ alignItems: 'center' }}>
      <View style={{ width: size, height: size }}>
        <Svg width={size} height={size}>
          {/* Background circle */}
          <Circle cx={center} cy={center} r={radius} stroke={theme.border} strokeWidth={strokeWidth} fill="none" />
          {/* Data segments */}
          {segments.map((seg, i) => (
            <Circle
              key={i}
              cx={center} cy={center} r={radius}
              stroke={seg.color}
              strokeWidth={strokeWidth}
              fill="none"
              strokeDasharray={`${circumference}`}
              strokeDashoffset={seg.offset}
              strokeLinecap="round"
              transform={`rotate(${seg.rotation}, ${center}, ${center})`}
            />
          ))}
        </Svg>
        {/* Center text */}
        <View style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ fontSize: 22, fontWeight: '800', color: theme.text }}>{data[0]?.value || 0}%</Text>
          <Text style={{ fontSize: 11, color: theme.textSecondary, marginTop: 2 }}>{data[0]?.label || ''}</Text>
        </View>
      </View>
      {/* Legend */}
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', marginTop: 14, gap: 14 }}>
        {data.map((d, i) => (
          <View key={i} style={{ flexDirection: 'row', alignItems: 'center' }}>
            <View style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: d.color, marginRight: 6 }} />
            <Text style={{ color: theme.textSecondary, fontSize: 12 }}>{d.label} {d.value}%</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

function StatCard({ icon, label, value, subtitle, color, theme }) {
  return (
    <View style={[s.statCard, { backgroundColor: theme.card, borderColor: theme.border }]}>
      <View style={[s.statIcon, { backgroundColor: color + '20' }]}><Ionicons name={icon} size={22} color={color} /></View>
      <Text style={[s.statValue, { color: theme.text }]}>{value}</Text>
      <Text style={[s.statLabel, { color: theme.textSecondary }]}>{label}</Text>
      {subtitle ? <Text style={[s.statSub, { color }]}>{subtitle}</Text> : null}
    </View>
  );
}

export default function DashboardScreen({ navigation }) {
  const { user } = useAuth(); const { theme } = useTheme(); const { t } = useLanguage();
  const [data, setData] = useState(null); const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true); const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const d = await api.getDashboard();
      setData(d);
    } catch (e) {
      setError('Unable to load dashboard. Pull down to retry.');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);
  const onRefresh = useCallback(async () => { setRefreshing(true); await load(); setRefreshing(false); }, [load]);

  if (loading) return <View style={[s.center, { backgroundColor: theme.background }]}><ActivityIndicator size="large" color={theme.primary} /></View>;

  if (error && !data) return (
    <ScrollView style={[s.container, { backgroundColor: theme.background }]} contentContainerStyle={s.center} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />}>
      <Ionicons name="cloud-offline-outline" size={48} color={theme.textSecondary} />
      <Text style={{ color: theme.textSecondary, fontSize: 16, marginTop: 12, textAlign: 'center', paddingHorizontal: 40 }}>{error}</Text>
    </ScrollView>
  );

  const ud = data?.user_data || {}; const trends = data?.pest_trends || { months: [], values: [] };
  const health = data?.health_distribution || {}; const dets = data?.recent_detections || [];
  const cc = { backgroundGradientFrom: theme.card, backgroundGradientTo: theme.card, color: (o=1) => theme.primary + Math.round(o*255).toString(16).padStart(2,'0'), labelColor: () => theme.textSecondary, decimalCount: 0, propsForDots: { r:'5', strokeWidth:'2', stroke: theme.primary } };
  const sevColor = sv => ({ Healthy: theme.success, High: theme.danger, Severe: theme.danger, Moderate: theme.warning }[sv] || theme.info);

  return (
    <ScrollView style={[s.container, { backgroundColor: theme.background }]} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.primary} />}>
      <View style={s.header}>
        <View style={{ flex:1 }}><Text style={[s.greeting, { color: theme.text }]}>{t('dashboard.greeting').replace('Farmer', user?.name||'Farmer')}</Text><Text style={[s.date, { color: theme.textSecondary }]}>{data?.current_date}</Text></View>
        <TouchableOpacity style={[s.scanBtn, { backgroundColor: theme.primary }]} onPress={() => navigation.navigate('Scan')}><Ionicons name="scan" size={20} color="#fff" /><Text style={s.scanBtnText}>{t('dashboard.scanButton')}</Text></TouchableOpacity>
      </View>
      <View style={s.statsGrid}>
        <StatCard icon="analytics" label={t('dashboard.totalScans')} value={ud.total_scans||0} subtitle={data?.weekly_change} color={theme.info} theme={theme} />
        <StatCard icon="leaf" label={t('dashboard.healthyPlants')} value={(ud.healthy_percentage||0)+'%'} color={theme.success} theme={theme} />
        <StatCard icon="bug" label={t('dashboard.pestsDetected')} value={ud.pests_detected||0} color={theme.danger} theme={theme} />
        <StatCard icon="hardware-chip" label={t('dashboard.aiAccuracy')} value={(ud.ai_accuracy||0)+'%'} color="#8b5cf6" theme={theme} />
      </View>
      {data?.weather && <View style={[s.wCard, { backgroundColor: theme.card, borderColor: theme.border }]}><Ionicons name="sunny" size={24} color="#f59e0b" /><View style={{ marginLeft: 12 }}><Text style={[s.wTemp, { color: theme.text }]}>{data.weather.temperature}°C - {data.weather.condition}</Text><Text style={{ color: theme.textSecondary, fontSize: 13 }}>Humidity: {data.weather.humidity}%</Text></View></View>}
      {trends.values.length > 0 && <View style={[s.section, { backgroundColor: theme.card, borderColor: theme.border }]}><Text style={[s.secTitle, { color: theme.text }]}>{t('dashboard.pestTrends')}</Text><LineChart data={{ labels: trends.months, datasets: [{ data: trends.values }] }} width={W-56} height={200} chartConfig={cc} bezier style={{ borderRadius: 12, marginTop: 8 }} /></View>}
      <View style={[s.section, { backgroundColor: theme.card, borderColor: theme.border }]}>
        <Text style={[s.secTitle, { color: theme.text }]}>{t('dashboard.plantHealthDist')}</Text>
        <DonutChart
          size={180}
          strokeWidth={24}
          theme={theme}
          data={[
            { label: t('dashboard.healthy'), value: health.healthy||0, color: '#10b981' },
            { label: t('dashboard.pestDamage'), value: health.pest_damage||0, color: '#f59e0b' },
            { label: t('dashboard.disease'), value: health.disease||0, color: '#ef4444' },
            { label: t('dashboard.critical'), value: health.critical||0, color: '#8b5cf6' },
          ]}
        />
      </View>
      <View style={[s.section, { backgroundColor: theme.card, borderColor: theme.border }]}>
        <View style={{ flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginBottom: 8 }}><Text style={[s.secTitle, { color: theme.text }]}>{t('dashboard.recentDetections')}</Text><TouchableOpacity onPress={() => navigation.getParent().navigate('History')}><Text style={{ color: theme.primary, fontWeight:'600' }}>{t('dashboard.viewAll')}</Text></TouchableOpacity></View>
        {dets.length === 0 ? <Text style={{ color: theme.textSecondary, textAlign: 'center', paddingVertical: 20 }}>No detections yet. Scan a plant to get started!</Text> : null}
        {dets.map((d,i) => <View key={i} style={[s.detRow, { borderBottomColor: theme.border }]}><View style={[s.dot, { backgroundColor: sevColor(d.severity) }]} /><View style={{ flex:1 }}><Text style={[s.detPest, { color: theme.text }]}>{d.pest}</Text><Text style={{ color: theme.textSecondary, fontSize: 12 }}>{d.crop} - {d.field}</Text></View><View style={{ alignItems:'flex-end' }}><Text style={[s.detPct, { color: theme.text }]}>{d.percentage}%</Text><Text style={{ color: theme.textSecondary, fontSize: 11 }}>{d.date}</Text></View></View>)}
      </View>
      <View style={[s.section, { backgroundColor: theme.card, borderColor: theme.border, marginBottom: 32 }]}>
        <Text style={[s.secTitle, { color: theme.text }]}>{t('dashboard.quickActions')}</Text>
        <View style={s.actionsRow}>{[{ icon:'scan', label:t('dashboard.scanNewLeaf'), screen:'Scan', color:theme.primary },{ icon:'time', label:t('dashboard.viewHistory'), screen:'History', color:theme.info },{ icon:'document-text', label:t('dashboard.exportReport'), screen:'History', color:'#8b5cf6' }].map((a,i) => <TouchableOpacity key={i} style={s.actBtn} onPress={() => navigation.navigate(a.screen)}><View style={[s.actIcon, { backgroundColor: a.color+'20' }]}><Ionicons name={a.icon} size={24} color={a.color} /></View><Text style={[s.actLabel, { color: theme.text }]}>{a.label}</Text></TouchableOpacity>)}</View>
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container:{flex:1}, center:{flex:1,justifyContent:'center',alignItems:'center'},
  header:{flexDirection:'row',justifyContent:'space-between',alignItems:'center',padding:20,paddingBottom:8},
  greeting:{fontSize:22,fontWeight:'700'}, date:{fontSize:13,marginTop:2},
  scanBtn:{flexDirection:'row',alignItems:'center',paddingHorizontal:16,paddingVertical:10,borderRadius:12}, scanBtnText:{color:'#fff',fontWeight:'700',marginLeft:6,fontSize:13},
  statsGrid:{flexDirection:'row',flexWrap:'wrap',paddingHorizontal:12},
  statCard:{width:'46%',margin:'2%',borderRadius:14,padding:16,borderWidth:1},
  statIcon:{width:40,height:40,borderRadius:12,alignItems:'center',justifyContent:'center',marginBottom:10},
  statValue:{fontSize:24,fontWeight:'800'}, statLabel:{fontSize:12,marginTop:2}, statSub:{fontSize:11,marginTop:4,fontWeight:'600'},
  wCard:{flexDirection:'row',alignItems:'center',marginHorizontal:16,marginTop:12,padding:16,borderRadius:14,borderWidth:1}, wTemp:{fontSize:16,fontWeight:'600'},
  section:{margin:16,marginBottom:0,borderRadius:14,padding:16,borderWidth:1}, secTitle:{fontSize:17,fontWeight:'700',marginBottom:8},
  detRow:{flexDirection:'row',alignItems:'center',paddingVertical:12,borderBottomWidth:1}, dot:{width:10,height:10,borderRadius:5,marginRight:12},
  detPest:{fontSize:15,fontWeight:'600'}, detPct:{fontSize:15,fontWeight:'700'},
  actionsRow:{flexDirection:'row',justifyContent:'space-around',marginTop:8}, actBtn:{alignItems:'center',width:90},
  actIcon:{width:52,height:52,borderRadius:16,alignItems:'center',justifyContent:'center',marginBottom:8}, actLabel:{fontSize:11,textAlign:'center',fontWeight:'600'},
});
