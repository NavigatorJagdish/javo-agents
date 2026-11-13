package com.javo.agents

import com.javo.agents.data.model.AgentCategory
import com.javo.agents.data.model.AgentRoster
import com.javo.agents.data.model.OperatingMode
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class OperatingModeTest {

    @Test
    fun testOperatingModesDefinedCorrectly() {
        assertEquals("Android Standalone", OperatingMode.ANDROID_STANDALONE.displayName)
        assertEquals("Windows Enhanced", OperatingMode.WINDOWS_ENHANCED.displayName)
        assertEquals("Cloud Mode", OperatingMode.CLOUD_MODE.displayName)

        assertTrue(OperatingMode.ANDROID_STANDALONE.badge.contains("Standalone"))
        assertTrue(OperatingMode.WINDOWS_ENHANCED.badge.contains("Windows"))
        assertTrue(OperatingMode.CLOUD_MODE.badge.contains("Cloud"))
    }

    @Test
    fun testAgentRosterAndroidCompatibility() {
        val allAgents = AgentRoster.allAgents
        assertEquals(29, allAgents.size)

        val androidCompatible = allAgents.filter { it.capability.isAndroidCompatible }
        assertTrue("At least 23 agents should be Android compatible", androidCompatible.size >= 23)

        val windowsOnly = allAgents.filter { it.capability.requiresWindows }
        assertTrue("Windows specialists should require Windows desktop runtime", windowsOnly.isNotEmpty())

        val contentFactory = allAgents.find { it.slug == "content_factory" }!!
        assertTrue(contentFactory.capability.isAndroidCompatible)
        assertFalse(contentFactory.capability.requiresWindows)

        val resourceOptimizer = allAgents.find { it.slug == "resource_optimizer" }!!
        assertFalse(resourceOptimizer.capability.isAndroidCompatible)
        assertTrue(resourceOptimizer.capability.requiresWindows)

        val selfUpgradingEngineer = allAgents.find { it.slug == "self_upgrading_engineer" }!!
        assertFalse(selfUpgradingEngineer.capability.isAndroidCompatible)
        assertTrue(selfUpgradingEngineer.capability.requiresWindows)

        val pluginTrust = allAgents.find { it.slug == "plugin_trust" }!!
        assertFalse(pluginTrust.capability.isAndroidCompatible)
        assertTrue(pluginTrust.capability.requiresWindows)
    }
}
