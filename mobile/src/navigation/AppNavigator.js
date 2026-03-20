import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import LoginScreen from '../screens/LoginScreen';
import RegisterScreen from '../screens/RegisterScreen';
import DashboardScreen from '../screens/DashboardScreen';
import ScanScreen from '../screens/ScanScreen';
import DescribeScreen from '../screens/DescribeScreen';
import ResultsScreen from '../screens/ResultsScreen';
import HistoryScreen from '../screens/HistoryScreen';
import SettingsScreen from '../screens/SettingsScreen';
import HelpScreen from '../screens/HelpScreen';
import AboutScreen from '../screens/AboutScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  const { theme } = useTheme(); const { t } = useLanguage();
  return (
    <Tab.Navigator screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        const icons = { Dashboard:'home', Scan:'scan', History:'time', Settings:'settings' };
        return <Ionicons name={focused ? icons[route.name] : icons[route.name]+'-outline'} size={size} color={color} />;
      },
      tabBarActiveTintColor: theme.primary, tabBarInactiveTintColor: theme.textSecondary,
      tabBarStyle: { backgroundColor:theme.card, borderTopColor:theme.border, height:88, paddingBottom:28, paddingTop:8 },
      headerStyle: { backgroundColor:theme.card }, headerTintColor: theme.text, headerShadowVisible: false,
    })}>
      <Tab.Screen name="Dashboard" component={DashboardScreen} options={{ title:t('nav.home') }} />
      <Tab.Screen name="Scan" component={ScanScreen} options={{ title:t('nav.scan') }} />
      <Tab.Screen name="History" component={HistoryScreen} options={{ title:t('nav.history') }} />
      <Tab.Screen name="Settings" component={SettingsScreen} options={{ title:t('nav.settings') }} />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  const { user, loading } = useAuth(); const { theme } = useTheme();
  if (loading) return null;
  return (
    <Stack.Navigator screenOptions={{ headerStyle:{ backgroundColor:theme.card }, headerTintColor:theme.text, headerShadowVisible:false, contentStyle:{ backgroundColor:theme.background } }}>
      {!user ? (
        <><Stack.Screen name="Login" component={LoginScreen} options={{ headerShown:false }} /><Stack.Screen name="Register" component={RegisterScreen} options={{ headerShown:false }} /></>
      ) : (
        <><Stack.Screen name="Main" component={MainTabs} options={{ headerShown:false }} /><Stack.Screen name="Describe" component={DescribeScreen} options={{ title:'Describe Symptoms' }} /><Stack.Screen name="Results" component={ResultsScreen} options={{ title:'Analysis Results' }} /><Stack.Screen name="Help" component={HelpScreen} options={{ title:'Help' }} /><Stack.Screen name="About" component={AboutScreen} options={{ title:'About' }} /></>
      )}
    </Stack.Navigator>
  );
}
