import path from "path"
import { fileURLToPath } from "url"

const pluginDir = path.dirname(fileURLToPath(import.meta.url))
const skillsDir = path.resolve(pluginDir, "../../skills")

export const SpecadiaPlugin = async () => ({
  config: async (config) => {
    config.skills = config.skills || {}
    config.skills.paths = config.skills.paths || []
    if (!config.skills.paths.includes(skillsDir)) {
      config.skills.paths.push(skillsDir)
    }

    config.command = config.command || {}
    if (!config.command["specadia-plan"]) {
      config.command["specadia-plan"] = {
        description: "Generate a traceable Specadia implementation plan",
        template: "Load and execute the `specadia-plan` skill.\n\n$ARGUMENTS",
      }
    }
  },
})

export default SpecadiaPlugin
