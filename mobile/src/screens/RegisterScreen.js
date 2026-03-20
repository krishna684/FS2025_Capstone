import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, ScrollView, Alert, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';

export default function RegisterScreen({ navigation }) {
  const { register } = useAuth();
  const { theme } = useTheme();
  const { t } = useLanguage();
  const [name, setName] = useState(''); const [email, setEmail] = useState('');
  const [phone, setPhone] = useState(''); const [location, setLocation] = useState('');
  const [password, setPassword] = useState(''); const [confirmPw, setConfirmPw] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleRegister() {
    if (!name || !email || !password) { Alert.alert(t('common.error'), 'Name, email, and password are required'); return; }
    if (password !== confirmPw) { Alert.alert(t('common.error'), 'Passwords do not match'); return; }
    setLoading(true);
    try { await register({ name, email, phone, location, password }); } catch (e) { Alert.alert(t('common.error'), e.message); } finally { setLoading(false); }
  }

  const I = (icon, ph, val, set, opts = {}) => (
    <View style={[styles.inputRow, { borderColor: theme.border, backgroundColor: theme.background }]}>
      <Ionicons name={icon} size={20} color={theme.textSecondary} />
      <TextInput style={[styles.input, { color: theme.text }]} placeholder={ph} placeholderTextColor={theme.textSecondary} value={val} onChangeText={set} {...opts} />
    </View>
  );

  return (
    <KeyboardAvoidingView style={[styles.container, { backgroundColor: theme.background }]} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={[styles.card, { backgroundColor: theme.card, borderColor: theme.border }]}>
          <Text style={[styles.title, { color: theme.text }]}>{t('register.title')}</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>{t('register.subtitle')}</Text>
          {I('person-outline', t('register.fullname'), name, setName)}
          {I('mail-outline', t('register.email'), email, setEmail, { autoCapitalize: 'none', keyboardType: 'email-address' })}
          {I('call-outline', t('register.phone'), phone, setPhone, { keyboardType: 'phone-pad' })}
          {I('location-outline', t('register.location'), location, setLocation)}
          {I('lock-closed-outline', t('register.password'), password, setPassword, { secureTextEntry: true })}
          {I('lock-closed-outline', t('register.confirm'), confirmPw, setConfirmPw, { secureTextEntry: true })}
          <TouchableOpacity style={[styles.button, { backgroundColor: theme.primary }]} onPress={handleRegister} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>{t('register.create')}</Text>}
          </TouchableOpacity>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.linkRow}>
            <Text style={{ color: theme.textSecondary, fontSize: 14 }}>{t('register.hasaccount')} </Text>
            <Text style={{ color: theme.primary, fontSize: 14, fontWeight: '700' }}>{t('register.signin')}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 }, scroll: { flexGrow: 1, justifyContent: 'center', padding: 20 },
  card: { borderRadius: 16, padding: 24, borderWidth: 1 },
  title: { fontSize: 24, fontWeight: '700', textAlign: 'center' },
  subtitle: { fontSize: 14, textAlign: 'center', marginTop: 4, marginBottom: 24 },
  inputRow: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: 12, paddingHorizontal: 14, height: 48, marginBottom: 14 },
  input: { flex: 1, marginLeft: 10, fontSize: 15 },
  button: { height: 50, borderRadius: 12, alignItems: 'center', justifyContent: 'center', marginTop: 8 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  linkRow: { flexDirection: 'row', justifyContent: 'center', marginTop: 20 },
});
