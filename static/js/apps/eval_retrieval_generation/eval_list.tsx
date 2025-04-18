/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* Component to show the full list of evaluation queries */

import React, { useContext, useState } from "react";
import { Button, Input, Modal } from "reactstrap";

import {
  NEW_QUERY_CALL_ID,
  QUERY_OVERALL_ANS_KEY,
  QUERY_OVERALL_QUESTIONS_KEY,
  RAG_CLAIM_KEYS,
} from "./constants";
import { AppContext, SessionContext } from "./context";
import { getAllFields, getCallCount, getPath } from "./data_store";
import { EvalType, Query } from "./types";
import { getFirstFeedbackStage } from "./util";

export function EvalList(): JSX.Element {
  const { allCall, allQuery, userEmail, sheetId, evalType } =
    useContext(AppContext);
  const { setSessionCallId, setSessionQueryId, setFeedbackStage } =
    useContext(SessionContext);

  const [userEvalsOnly, setUserEvalsOnly] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [queryCompletionStatus, setQueryCompletionStatus] = useState({});

  const toggleModal = (): void => setModalOpen(!modalOpen);

  const orderedQueries: Query[] = Object.keys(allQuery)
    .sort((a, b) => {
      return Number(a) - Number(b);
    })
    .map((queryId) => allQuery[queryId]);

  const openModal = (): void => {
    setModalOpen(true);
    const queryFeedbackPromises = Promise.all(
      orderedQueries.map((query) => getAllFields(getPath(sheetId, query.id)))
    );
    const callCountPromises = Promise.all(
      orderedQueries.map((query) => getCallCount(sheetId, query.id))
    );
    const queryCompletionStatus = {};
    Promise.all([callCountPromises, queryFeedbackPromises])
      .then(([callCountResults, queryFeedbackResults]) => {
        orderedQueries.forEach((query, i) => {
          // A query might not have any calls.
          const calls = allCall[query.id] || {};
          let completed = callCountResults[i] === Object.keys(calls).length;
          // If no overall feedback value, set completed to false
          if (!queryFeedbackResults[i][QUERY_OVERALL_ANS_KEY]) {
            completed = false;
          }
          // For RAG eval type, also check that additional feedback is completed
          if (evalType === EvalType.RAG) {
            [
              ...Object.values(RAG_CLAIM_KEYS),
              QUERY_OVERALL_QUESTIONS_KEY,
            ].forEach((countKey) => {
              if (!(countKey in queryFeedbackResults[i])) {
                completed = false;
              }
            });
          }
          queryCompletionStatus[query.id] = completed;
        });
        setQueryCompletionStatus(queryCompletionStatus);
      })
      .finally(() => {
        setQueryCompletionStatus(queryCompletionStatus);
      });
  };

  return (
    <>
      <Button className="eval-list-button" onClick={openModal}>
        <div>
          <span className="material-icons-outlined">list_alt</span>
          Evaluation list
        </div>
      </Button>
      <Modal
        className="eval-list-modal"
        isOpen={modalOpen}
        toggle={toggleModal}
      >
        <div className="header">
          <div className="title">Choose a query to start evaluating from</div>
          <div className="subtitle">
            <div className="subtitle-message">
              Select a query to start evaluating, evaluated queries are marked
              in green.
            </div>
            <div className="filter-checkbox">
              <Input
                type="checkbox"
                checked={userEvalsOnly}
                onChange={(): void => {
                  setUserEvalsOnly(!userEvalsOnly);
                }}
              />
              <span>Show my questions only</span>
            </div>
          </div>
        </div>
        <div className="body">
          {orderedQueries.map((query) => {
            if (userEvalsOnly && query.user !== userEmail) {
              return null;
            }
            const completed = queryCompletionStatus[query.id];
            return (
              <div
                className={`eval-list-query${completed ? " completed" : ""}`}
                onClick={(): void => {
                  setFeedbackStage(getFirstFeedbackStage(evalType));
                  setSessionQueryId(query.id);
                  setSessionCallId(NEW_QUERY_CALL_ID);
                  setModalOpen(false);
                }}
                key={query.id}
              >
                <div className="material-icons-outlined">
                  {completed ? "check" : "chevron_right"}
                </div>
                <div className="query-name">
                  Q{query.id} &#183; {query.text}
                </div>
                <div className="user">{query.user}</div>
              </div>
            );
          })}
        </div>
        <div className="footer">
          <Button
            onClick={(): void => setModalOpen(false)}
            className="btn-transparent"
          >
            <div>Close</div>
          </Button>
        </div>
      </Modal>
    </>
  );
}
