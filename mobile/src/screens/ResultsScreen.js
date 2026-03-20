import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Image, Animated, TextInput, Alert, Dimensions } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import api from '../services/api';

const { width: SW } = Dimensions.get('window');

function Badge({ severity, theme }) {
  const c = { Healthy:theme.success, Mild:'#3b82f6', Moderate:'#f59e0b', High:theme.danger, Severe:theme.danger }[severity] || theme.textSecondary;
  return <View style={[s.badge, { backgroundColor: c+'20' }]}><Text style={[s.badgeText, { color: c }]}>{severity}</Text></View>;
}

function Treatments({ title, icon, items, color, theme }) {
  if (!items || !items.length) return null;
  return (
    <View style={[s.treatCard, { backgroundColor: color+'08', borderColor: color+'30' }]}>
      <View style={s.treatHead}><Ionicons name={icon} size={20} color={color} /><Text style={[s.treatTitle, { color }]}>{title}</Text></View>
      {items.map((it,i) => <View key={i} style={s.treatRow}><Text style={{ color, fontSize:16, marginRight:8 }}>{'\u2022'}</Text><Text style={[s.treatText, { color: theme.text }]}>{it}</Text></View>)}
    </View>
  );
}

// Scan point overlay on the analyzed image
function ScanPointsOverlay({ result, theme }) {
  const dots = useRef([...Array(5)].map(() => new Animated.Value(0))).current;
  const isHealthy = result.status === 'Healthy' || result.pest_identified === 'None';
  const color = isHealthy ? theme.success : theme.danger;

  // Predefined scan point positions (percentage-based)
  const points = [
    { x: '20%', y: '25%' },
    { x: '55%', y: '35%' },
    { x: '35%', y: '60%' },
    { x: '70%', y: '55%' },
    { x: '45%', y: '80%' },
  ];

  useEffect(() => {
    Animated.stagger(200, dots.map(d =>
      Animated.spring(d, { toValue: 1, friction: 4, tension: 80, useNativeDriver: true })
    )).start();
  }, []);

  return (
    <View style={StyleSheet.absoluteFill}>
      {points.map((pt, i) => (
        <Animated.View key={i} style={{
          position: 'absolute', left: pt.x, top: pt.y,
          opacity: dots[i],
          transform: [{ scale: dots[i].interpolate({ inputRange: [0,1], outputRange: [0, 1] }) }]
        }}>
          {/* Outer pulse ring */}
          <View style={{ width: 28, height: 28, borderRadius: 14, borderWidth: 1.5, borderColor: color+'80', alignItems: 'center', justifyContent: 'center', marginLeft: -14, marginTop: -14 }}>
            {/* Inner dot */}
            <View style={{ width: 12, height: 12, borderRadius: 6, backgroundColor: color, shadowColor: color, shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.6, shadowRadius: 6 }} />
          </View>
          {/* Label */}
          {i === 0 && !isHealthy && (
            <View style={{ position: 'absolute', top: -28, left: -10, backgroundColor: 'rgba(0,0,0,0.75)', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 }}>
              <Text style={{ color: '#fff', fontSize: 10, fontWeight: '700' }}>Detected</Text>
            </View>
          )}
        </Animated.View>
      ))}

      {/* Status badge on image */}
      <View style={{ position: 'absolute', bottom: 12, left: 12, flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.7)', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20 }}>
        <Ionicons name={isHealthy ? 'checkmark-circle' : 'alert-circle'} size={16} color={color} />
        <Text style={{ color: '#fff', fontSize: 12, fontWeight: '700', marginLeft: 6 }}>
          {isHealthy ? 'Healthy' : result.pest_identified}
        </Text>
      </View>

      {/* Confidence badge */}
      <View style={{ position: 'absolute', bottom: 12, right: 12, backgroundColor: 'rgba(0,0,0,0.7)', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 20 }}>
        <Text style={{ color: theme.primary, fontSize: 12, fontWeight: '800' }}>{Math.round(result.confidence || 0)}%</Text>
      </View>
    </View>
  );
}

// Feedback section
function FeedbackSection({ result, theme }) {
  const [submitted, setSubmitted] = useState(false);
  const [showCorrection, setShowCorrection] = useState(false);
  const [correctPest, setCorrectPest] = useState('');
  const [notes, setNotes] = useState('');
  const [pests, setPests] = useState([]);

  if (submitted) return (
    <View style={[s.feedbackCard, { backgroundColor: theme.success+'15', borderColor: theme.success+'40' }]}>
      <Ionicons name="checkmark-circle" size={32} color={theme.success} />
      <Text style={{ color: theme.success, fontWeight: '700', fontSize: 16, marginTop: 8 }}>Thank you for your feedback!</Text>
      <Text style={{ color: theme.textSecondary, fontSize: 13, marginTop: 4 }}>Your input helps improve AGBOT</Text>
    </View>
  );

  async function loadPests() {
    try { const p = await api.getPests(); setPests(p); } catch(e) {}
  }

  async function submitFeedback(isCorrect) {
    try {
      await api.submitFeedback({
        scan_id: result.scan_id,
        is_correct: isCorrect,
        actual_pest_name: correctPest || null,
        notes: notes || null,
      });
      setSubmitted(true);
    } catch (e) {
      Alert.alert('Error', 'Failed to submit feedback. Please try again.');
    }
  }

  return (
    <View style={[s.feedbackCard, { backgroundColor: '#fef3c7', borderColor: '#fbbf24' }]}>
      <Ionicons name="help-circle" size={36} color="#f59e0b" />
      <Text style={{ color: '#92400e', fontWeight: '700', fontSize: 17, marginTop: 8 }}>Is this result correct?</Text>
      <Text style={{ color: '#a16207', fontSize: 13, marginTop: 4, textAlign: 'center' }}>
        AI confidence: {Math.round(result.confidence || 0)}%. Help us improve!
      </Text>

      <View style={{ flexDirection: 'row', marginTop: 16, gap: 10 }}>
        <TouchableOpacity
          style={{ flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', height: 46, borderRadius: 12, backgroundColor: '#d1fae5', borderWidth: 2, borderColor: '#10b981' }}
          onPress={() => submitFeedback(true)}
        >
          <Ionicons name="checkmark" size={20} color="#065f46" />
          <Text style={{ color: '#065f46', fontWeight: '700', marginLeft: 6 }}>Correct</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={{ flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', height: 46, borderRadius: 12, backgroundColor: '#fee2e2', borderWidth: 2, borderColor: '#ef4444' }}
          onPress={() => { setShowCorrection(true); loadPests(); }}
        >
          <Ionicons name="close" size={20} color="#991b1b" />
          <Text style={{ color: '#991b1b', fontWeight: '700', marginLeft: 6 }}>Incorrect</Text>
        </TouchableOpacity>
      </View>

      {showCorrection && (
        <View style={{ marginTop: 16, width: '100%' }}>
          <Text style={{ color: '#92400e', fontWeight: '600', marginBottom: 8 }}>What is the correct pest?</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 12 }}>
            {pests.map((p, i) => (
              <TouchableOpacity key={i} style={{
                paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, marginRight: 8,
                backgroundColor: correctPest === p.common_name ? '#10b981' : '#fff',
                borderWidth: 1, borderColor: correctPest === p.common_name ? '#10b981' : '#d1d5db',
              }} onPress={() => setCorrectPest(p.common_name)}>
                <Text style={{ color: correctPest === p.common_name ? '#fff' : '#374151', fontSize: 13, fontWeight: '600' }}>{p.common_name}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
          <TextInput
            style={{ backgroundColor: '#fff', borderRadius: 10, padding: 12, borderWidth: 1, borderColor: '#d1d5db', fontSize: 14, minHeight: 60, textAlignVertical: 'top' }}
            placeholder="Additional notes (optional)"
            placeholderTextColor="#9ca3af"
            value={notes}
            onChangeText={setNotes}
            multiline
          />
          <TouchableOpacity
            style={{ marginTop: 12, height: 44, borderRadius: 12, backgroundColor: '#f59e0b', alignItems: 'center', justifyContent: 'center' }}
            onPress={() => submitFeedback(false)}
          >
            <Text style={{ color: '#fff', fontWeight: '700' }}>Submit Correction</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

export default function ResultsScreen({ route, navigation }) {
  const { theme } = useTheme(); const { t } = useLanguage();
  const { result, type, imageUri } = route.params || {};
  if (!result) return <View style={[s.center, { backgroundColor: theme.background }]}><Text style={{ color: theme.textSecondary }}>No results</Text></View>;

  const isHealthy = result.status === 'Healthy' || result.pest_identified === 'None';
  const pest = result.pest_identified || result.disease_name || 'Unknown';
  const sci = result.pest_scientific || result.scientific_name || '';
  const conf = result.confidence || 0; const sev = result.severity || 'Unknown';
  const tx = result.treatments || {}; const chem = result.chemical_treatments || []; const org = result.organic_treatments || [];
  const prev = result.prevention || tx.prevention || []; const causes = result.causes || [];
  const symptoms = result.symptoms || [];
  const allPreds = result.all_predictions || [];
  const affected = result.affected_plants || [];

  return (
    <ScrollView style={[s.container, { backgroundColor: theme.background }]} contentContainerStyle={{ padding:20, paddingBottom:40 }}>
      {/* Scanned image with scan points */}
      {imageUri && (
        <View style={{ borderRadius: 16, overflow: 'hidden', marginBottom: 16, position: 'relative' }}>
          <Image source={{ uri: imageUri }} style={{ width: '100%', height: 260, borderRadius: 16 }} />
          <ScanPointsOverlay result={result} theme={theme} />
        </View>
      )}

      {/* Status card */}
      <View style={[s.statusCard, { backgroundColor: (isHealthy ? theme.success : theme.danger)+'15', borderColor: (isHealthy ? theme.success : theme.danger)+'40' }]}>
        <Ionicons name={isHealthy ? 'checkmark-circle' : 'warning'} size={48} color={isHealthy ? theme.success : theme.danger} />
        <Text style={[s.statusText, { color: isHealthy ? theme.success : theme.danger }]}>{isHealthy ? 'Plant is Healthy!' : t('results.detected')}</Text>
        {!isHealthy ? <Text style={[s.pestName, { color: theme.text }]}>{pest}</Text> : null}
        {sci && !isHealthy ? <Text style={{ color: theme.textSecondary, fontSize:14, fontStyle:'italic', marginTop:2 }}>({sci})</Text> : null}
      </View>

      {/* Confidence */}
      <View style={[s.details, { backgroundColor: theme.card, borderColor: theme.border }]}>
        <View style={s.detailRow}>
          <Text style={[s.detailLabel, { color: theme.textSecondary }]}>{t('results.confidence')}</Text>
          <View style={s.confRow}>
            <View style={[s.confBar, { backgroundColor: theme.border }]}>
              <View style={[s.confFill, { width: conf+'%', backgroundColor: conf>80 ? theme.success : theme.warning }]} />
            </View>
            <Text style={[s.confText, { color: theme.text }]}>{Math.round(conf)}%</Text>
          </View>
        </View>
        <View style={[s.divider, { backgroundColor: theme.border }]} />
        <View style={s.detailRow}>
          <Text style={[s.detailLabel, { color: theme.textSecondary }]}>{t('results.severity')}</Text>
          <Badge severity={sev} theme={theme} />
        </View>
        {result.damage_pattern ? <>
          <View style={[s.divider, { backgroundColor: theme.border }]} />
          <View style={s.detailRow}>
            <Text style={[s.detailLabel, { color: theme.textSecondary }]}>Description</Text>
            <Text style={{ color: theme.text, fontSize:14, lineHeight:20 }}>{result.damage_pattern}</Text>
          </View>
        </> : null}
      </View>

      {/* Alternative predictions */}
      {allPreds.length > 1 && (
        <View style={[s.altCard, { backgroundColor: theme.card, borderColor: theme.border }]}>
          <Text style={[s.detailLabel, { color: theme.textSecondary, marginBottom: 8 }]}>Other Possibilities</Text>
          {allPreds.slice(1).map((p, i) => (
            <View key={i} style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 6 }}>
              <Text style={{ color: theme.text, fontSize: 14 }}>{p.pest}</Text>
              <Text style={{ color: theme.textSecondary, fontSize: 13, fontWeight: '700' }}>{Math.round(p.confidence)}%</Text>
            </View>
          ))}
        </View>
      )}

      {/* Symptoms */}
      {symptoms.length > 0 && <Treatments title="Symptoms" icon="eye-outline" items={symptoms} color={theme.warning} theme={theme} />}

      {/* Causes */}
      {causes.length > 0 && <Treatments title="Causes" icon="information-circle" items={causes} color={theme.info} theme={theme} />}

      {/* Treatments */}
      {!isHealthy && tx.immediate?.length > 0 && <Treatments title="Immediate Actions" icon="flash" items={tx.immediate} color={theme.danger} theme={theme} />}
      {!isHealthy && tx.ipm?.length > 0 && <Treatments title="IPM Treatments" icon="leaf" items={tx.ipm} color={theme.primary} theme={theme} />}
      {chem.length > 0 && <Treatments title="Chemical Treatments" icon="flask" items={chem} color={theme.warning} theme={theme} />}
      {org.length > 0 && <Treatments title="Organic Treatments" icon="leaf" items={org} color={theme.success} theme={theme} />}
      {prev.length > 0 && <Treatments title={t('results.prevention')} icon="shield-checkmark" items={prev} color="#8b5cf6" theme={theme} />}

      {/* Affected plants */}
      {affected.length > 0 && (
        <View style={[s.affectedCard, { backgroundColor: theme.card, borderColor: theme.border }]}>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 10 }}>
            <Ionicons name="leaf" size={18} color={theme.primary} />
            <Text style={{ color: theme.text, fontWeight: '700', fontSize: 15, marginLeft: 8 }}>Affected Plants</Text>
          </View>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
            {affected.map((p, i) => (
              <View key={i} style={{ backgroundColor: theme.primary+'15', paddingHorizontal: 12, paddingVertical: 5, borderRadius: 16 }}>
                <Text style={{ color: theme.primary, fontSize: 12, fontWeight: '600' }}>{p}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Feedback */}
      <FeedbackSection result={result} theme={theme} />

      {/* Action buttons */}
      <View style={{ flexDirection:'row', marginTop:8 }}>
        <TouchableOpacity style={[s.actBtn, { backgroundColor: theme.primary }]} onPress={() => navigation.navigate('Main', { screen: 'Scan' })}><Ionicons name="scan" size={20} color="#fff" /><Text style={s.actBtnText}>{t('results.newscan')}</Text></TouchableOpacity>
        <TouchableOpacity style={[s.actBtnO, { borderColor: theme.primary }]} onPress={() => navigation.navigate('Main', { screen: 'History' })}><Ionicons name="time" size={20} color={theme.primary} /><Text style={[s.actBtnOText, { color: theme.primary }]}>View History</Text></TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container:{flex:1}, center:{flex:1,justifyContent:'center',alignItems:'center'},
  statusCard:{borderRadius:16,padding:24,alignItems:'center',borderWidth:1,marginBottom:16},
  statusText:{fontSize:20,fontWeight:'800',marginTop:12}, pestName:{fontSize:24,fontWeight:'700',marginTop:4},
  details:{borderRadius:14,padding:16,borderWidth:1,marginBottom:16}, detailRow:{paddingVertical:10},
  detailLabel:{fontSize:13,fontWeight:'600',marginBottom:6}, divider:{height:1},
  confRow:{flexDirection:'row',alignItems:'center'}, confBar:{flex:1,height:8,borderRadius:4,marginRight:10}, confFill:{height:8,borderRadius:4}, confText:{fontSize:16,fontWeight:'700',width:50},
  badge:{alignSelf:'flex-start',paddingHorizontal:14,paddingVertical:4,borderRadius:12}, badgeText:{fontSize:13,fontWeight:'700'},
  treatCard:{borderRadius:14,padding:16,borderWidth:1,marginBottom:12}, treatHead:{flexDirection:'row',alignItems:'center',marginBottom:10},
  treatTitle:{fontSize:15,fontWeight:'700',marginLeft:8}, treatRow:{flexDirection:'row',marginBottom:6,paddingLeft:4}, treatText:{fontSize:14,lineHeight:20,flex:1},
  altCard:{borderRadius:14,padding:16,borderWidth:1,marginBottom:12},
  affectedCard:{borderRadius:14,padding:16,borderWidth:1,marginBottom:12},
  feedbackCard:{borderRadius:16,padding:20,borderWidth:2,marginBottom:16,alignItems:'center'},
  actBtn:{flex:1,flexDirection:'row',alignItems:'center',justifyContent:'center',height:50,borderRadius:12,marginRight:6}, actBtnText:{color:'#fff',fontWeight:'700',marginLeft:8},
  actBtnO:{flex:1,flexDirection:'row',alignItems:'center',justifyContent:'center',height:50,borderRadius:12,borderWidth:2,marginLeft:6}, actBtnOText:{fontWeight:'700',marginLeft:8},
});
