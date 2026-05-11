import React, { useState, useEffect } from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import OnboardingScreen from '../screens/OnboardingScreen';
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
import ChatScreen from '../screens/ChatScreen';
import PestLibraryScreen from '../screens/PestLibraryScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  const { theme } = useTheme(); const { t } = useLanguage();
  return (
    <Tab.Navigator screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        const icons = { Dashboard:'home', Scan:'scan', Chat:'chatbubbles', Library:'book', Settings:'settings' };
        return <Ionicons name={focused ? icons[route.name] : icons[route.name]+'-outline'} size={size} color={color} />;
      },
      tabBarActiveTintColor: theme.primary, tabBarInactiveTintColor: theme.textSecondary,
      tabBarStyle: { backgroundColor:theme.card, borderTopColor:theme.border, height:88, paddingBottom:28, paddingTop:8 },
      headerStyle: { backgroundColor:theme.card }, headerTintColor: theme.text, headerShadowVisible: false,
    })}>
      <Tab.Screen name="Dashboard" component={DashboardScreen} options={{ title: t('nav.home') }} />
      <Tab.Screen name="Scan" component={ScanScreen} options={{ title: t('nav.scan') }} />
      <Tab.Screen name="Chat" component={ChatScreen} options={{ title: 'Chat' }} />
      <Tab.Screen name="Library" component={PestLibraryScreen} options={{ title: 'Pests' }} />
      <Tab.Screen name="Settings" component={SettingsScreen} options={{ title: t('nav.settings') }} />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  const { user, loading } = useAuth(); const { theme } = useTheme();
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [checkingOnboarding, setCheckingOnboarding] = useState(true);

  // Check if we need to show onboarding after a new registration
  useEffect(() => {
    if (!user) {
      setShowOnboarding(false);
      setCheckingOnboarding(false);
      return;
    }
    // User is logged in — check if they just registered
    AsyncStorage.getItem('show_onboarding_after_register').then(val => {
      if (val === 'true') {
        setShowOnboarding(true);
      }
      setCheckingOnboarding(false);
    });
  }, [user]);

  if (loading || checkingOnboarding) return null;

  // Not logged in — show auth screens
  if (!user) {
    return (
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Register" component={RegisterScreen} />
      </Stack.Navigator>
    );
  }

  // Just registered — show onboarding
  if (showOnboarding) {
    return (
      <OnboardingScreen onComplete={async () => {
        await AsyncStorage.removeItem('show_onboarding_after_register');
        setShowOnboarding(false);
      }} />
    );
  }

  // Logged in — show main app
  return (
    <Stack.Navigator screenOptions={{ headerStyle:{ backgroundColor:theme.card }, headerTintColor:theme.text, headerShadowVisible:false, contentStyle:{ backgroundColor:theme.background } }}>
      <Stack.Screen name="Main" component={MainTabs} options={{ headerShown:false }} />
      <Stack.Screen name="Describe" component={DescribeScreen} options={{ title:'Describe Symptoms' }} />
      <Stack.Screen name="Results" component={ResultsScreen} options={{ title:'Analysis Results' }} />
      <Stack.Screen name="History" component={HistoryScreen} options={{ title:'Scan History' }} />
      <Stack.Screen name="Help" component={HelpScreen} options={{ title:'Help' }} />
      <Stack.Screen name="About" component={AboutScreen} options={{ title:'About' }} />
    </Stack.Navigator>
  );
}
