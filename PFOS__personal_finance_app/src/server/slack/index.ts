/**
 * Slack adapter exports. Owning authority: Contract 14 §11 / Phase 14.3 Stage 1, D-7 Reading A.
 * Importing this barrel creates no adapter and opens no connection.
 */
export {
  createSlackSocketModeAdapter,
  type SlackAdmissionPort,
  type SlackControlSink,
  type SlackMessageSender,
  type SlackSocketModeAdapter,
  type SlackSocketModeDependencies,
} from './socketModeAdapter.ts';
